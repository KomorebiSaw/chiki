#coding: utf-8
from chiki.admin import ModelView
from chiki.admin.formatters import formatter_len
from flask.ext.admin import expose
from .models import WXMenu
from chiki import json_error, json_success
from flask import current_app


class WXMenuView(ModelView):
    column_list = ('name', 'second', 'url', 'make', 'sort', 'created')
    column_center_list = ('name', 'second', 'url', 'created')
    column_formatters = dict(
        second=formatter_len(100),
    )

    script = """
$(function(){
    $(document).ready(function(){
        var html = '<li class="this_go" style="float:right;"><div class="btn btn-primary" >更新菜单</div></li>';
        $(".nav-tabs").append(html);
        $(".this_go").click(function(){
            var result = confirm('是否更新菜单')
            if(result==true){
                $.get('/admin/wxmenu/create_menu', function(data){
                    if(data.code==0){
                        console.log('let is go!')
                    } else if(data.code==1){
                        console.log('oh, my god!')
                    }
                })
            }else{
                console.log('退出更新！')
            }
        })
    })
})
"""

    @expose('/create_menu')
    def create(self):
        wxmenus = WXMenu.objects(make=True).order_by('sort').limit(3)
        buttons = list()
        if not wxmenus:
            return json_error()
        for wxmenu in wxmenus:
            if wxmenu.second:
                button_two = dict(name=wxmenu.name)
                two_list = list()
                for second in wxmenu.second:
                    this_dict = dict(type='view', name=second.name, url=second.url)
                    two_list.append(this_dict)
                button_two['sub_button'] = two_list
                buttons.append(button_two)
            else:
                this_dict = dict(type='view', name=wxmenu.name, url=wxmenu.url)
                buttons.append(this_dict)

        current_app.wxclient.create_menu(dict(button=buttons))
        return json_success()
