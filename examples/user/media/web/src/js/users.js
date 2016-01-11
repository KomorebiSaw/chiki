/*
 * users.js - v1.0.0 - 2016-01-10
 * home: http://www.haoku.net/
 * Copyright (c) 2016 XiaoKu Inc. All Rights Reserved.
 */

 + function ($) {

    'use strict'

    var $K = window.$K || {}

    var texts = {
        SEND_PHONE_CODE: '发送验证码',
        SEND_SUCCESS: '发送成功',
        SENDING: '正在发送...',
        ACCESSING: '正在验证...',
        NEXT: '下一步',
        REGISTER_COMPLETE: '完成注册',
        REGISTER_SUCCESS: '注册成功',
        RESET_COMPLETE: '设置',
        RESET_SUCCESS: '设置成功',
        UNKNOWN_ERROR: '未知错误',
        REPASSWORD_DIFF: '两次密码不一致',
        LOGINING: '正在登录...',
        LOGIN_SUCCESS: '登录成功'
    }

    var urls = {
        LOGIN: '/users/login',
        REGISTER_EMAIL: '/users/register/email',
        REGISTER_EMAIL_SEND: '/users/sendcode/email?action=register',
        REGISTER_PHONE: '/users/register/phone',
        REGISTER_PHONE_SEND: '/users/sendcode/phone?action=register',
        REGISTER_PHONE_ACCESS: '/users/authcode/phone?action=register',
        REGISTER_NEXT: '/users/login.html',
        RESET_PASSWORD_EMAIL: '/users/reset_password/email',
        RESET_PASSWORD_EMAIL_SEND: '/users/sendcode/email?action=reset_password',
        RESET_PASSWORD_PHONE: '/users/reset_password/phone',
        RESET_PASSWORD_PHONE_SEND: '/users/sendcode/phone?action=reset_password',
        RESET_PASSWORD_PHONE_ACCESS: '/users/authcode/phone?action=reset_password',
        RESET_PASSWORD_NEXT:'/users/login.html'
    }

    var onBtnSubmit = function (form, event, btn, options) {
        form.on(event, function () {
            if (options.before !== undefined) options.before()
            if (options.resetText !== undefined) btn.data('reset-text', options.resetText)
            if (options.loadingText !== undefined) btn.data('loading-text', options.loadingText)
            if (options.completeText !== undefined) btn.data('complete-text', options.completeText)
            btn.button('loading')
            if (options.check === undefined || options.check()) {
                var ajaxOptions = {
                    success: function (data) {
                        if (data.code === 0) {
                            form.off(event)
                            if (options.success !== undefined) {
                                options.success(data)
                            }
                            btn.button('complete')
                        } else {
                            $K.error(data.msg)
                            if (options.error !== undefined) {
                                options.error(data)
                            }
                            btn.button('reset')
                        }
                    },
                    error: function () {
                        $K.error(texts.UNKNOWN_ERROR)
                        if (options.error !== undefined) {
                            options.error()
                        }
                        btn.button('reset')
                    }
                }
                if (options.url !== undefined) ajaxOptions.url = options.url
                if (options.data !== undefined) ajaxOptions.data = options.data
                if (options.type !== undefined) ajaxOptions.type = options.data
                form.ajaxSubmit(ajaxOptions)
            } else {
                if (options.cancel !== undefined) {
                    options.cancel()
                }
                btn.button('reset')
            }
            return false
        })
    }

    var Resend = function (options) {
        this.options = $.extend({}, Resend.DEFAULTS, typeof options === 'object' && options)
    }

    Resend.DEFAULTS = {
        form: '.form',
        resend: '.resend',
        resendText: '重新发送',
        seconds: 60
    }

    Resend.prototype.start = function () {
        var $resend = $(this.options.resend)
        var seconds = this.options.seconds
        this.stop()
        $resend.text(this.options.resendText + ' ' + seconds)
        this.interval = setInterval($.proxy(function () {
            if (seconds === 0) {
                this.stop()
                this.click()
            } else {
                seconds -= 1
                $resend.text(this.options.resendText + ' ' + seconds)
            }
        }, this), 1000)
        $resend.show()
        $resend.addClass('disabled')
        $K.hide()
    }

    Resend.prototype.resend = function () {
        var $form = $(this.options.form)
        var $resend = $(this.options.resend)
        $resend.off('click')
        if (this.options.check === undefined || this.options.check()) {
            var options = {
                success: $.proxy(function (data) {
                    if (data.code === 0) {
                        this.start()
                    } else {
                        this.click()
                        $K.error(data.msg)
                    }
                }, this),
                error: $.proxy(function () {
                    this.click()
                    $K.error(texts.UNKNOWN_ERROR)
                })
            }
            if (this.options.url !== undefined) options.url = this.options.url
            $form.ajaxSubmit(options)
        }
    }

    Resend.prototype.stop = function () {
        var $resend = $(this.options.resend)
        if (this.interval !== undefined) {
            clearInterval(this.interval)
            this.interval = undefined
            $resend.text(this.options.resendText)
            $resend.removeClass('disabled')
            $resend.off('click')
        }
    }

    Resend.prototype.click = function () {
        var $resend = $(this.options.resend)
        $resend.on('click', $.proxy(function () {
            this.resend()
        }, this))
    }

    var Login = function (options) {
        if ($('.login-form').length === 0) return

        var form = $('.login-form')
        var account = form.find('#account')
        var password = form.find('#password')
        var code = form.find('#verify_code')
        var btn = form.find('[type="submit"]')

        options = $.extend({}, typeof options == 'object' && options)
        
        account.check({})
        password.check({strip:false})
        code.check({})

        onBtnSubmit(form, 'submit.account', btn, {
            url: urls.LOGIN,
            loadingText: texts.LOGINING,
            completeText: texts.LOGIN_SUCCESS,
            check: function () { return account.check() && password.check() && code.check() },
            success: function (data) {
                if (options.success !== undefined) {
                    options.success(data)
                } else {
                    window.location.reload()
                }
            },
            error: function (data) {
                if (data !== undefined && data.refresh === true) {
                    var src = $('.login-form #verify_code_img').data('src') + '&t=' + Math.random()
                    $('.login-form #verify_code_img').attr('src', src)
                }
            }
        })

        $K.hide()
    }

    var Register = function (options) {
        if (options === 'phone') {
            Register.phone()
        } else {
            Register.email()
        }
    }

    Register.emailResend = new Resend({
        form: '.register-email-form',
        resend: '.register-email .resend',
        url: urls.REGISTER_EMAIL_SEND,
        check: function () { return $('.register-email-form #email').check() }
    })

    Register.email = function () {
        if ($('.register-email').length > 0) {
            Register.emailOff()
            Register.phoneOff()
            Register.emailSend()
            $('.register-email, .register-email-form').show()
            $('.register-email .use-phone').on('click', function () {
                Register.phone()
            })
        } else if ($('.register-email-access').length > 0) {
            Register.emailComplete()
        }
    }

    Register.emailOff = function () {
        Register.emailResend.stop()
        $('.register-email').hide()
        $('.register-email-form').off('submit.email.send')
        $('.email-access').html('')
        $K.hide()
    }

    Register.emailSend = function () {
        var form = $('.register-email-form')
        var email = form.find('#email')
        var code = form.find('#verify_code')
        var btn = form.find('[type="submit"]')
        var regx = /^[\w\d]+[\d\w_.]+@([\d\w]+)\.([\d\w]+)(?:\.[\d\w]+)?$/
        code.check({})
        email.check({ max: 40, regx: { re: regx } })

        onBtnSubmit(form, 'submit.email.send', btn, {
            url: urls.REGISTER_EMAIL_SEND,
            loadingText: texts.SENDING,
            completeText: texts.REGISTER_SUCCESS,
            check: function () { return email.check() && code.check() },
            success: function (data) { Register.emailAccess(email.val(), data.data.email_url) },
            error: function (data) {
                if (data !== undefined && data.refresh === true) {
                    var src = $('.register-email #verify_code_img').data('src') + '&t=' + Math.random()
                    $('.register-email #verify_code_img').attr('src', src)
                }
            }
        })

        $K.hide()
    }

    Register.emailAccess = function (email, url) {
        $('.register-email-form').hide()
        $('.register-email .email-access').html('')
        $('<div><p>验证邮件已发送, ' +
            '请<a href="${ url }" target="_blank">点击查收邮件</a>激活账号。</p>' +
            '没有收到邮件？请耐心等待，或者<a class="resend" href="javascript:;">重新发送</a></div>')
            .tmpl({ email: email, url: url })
            .appendTo('.register-email .email-access')
        Register.emailResend.start()
        $K.hide()
    }

    Register.emailComplete = function () {
        var form = $('.register-email-access-form')
        var phone = form.find('#phone')
        var username = form.find('#username')
        var password = form.find('#password')
        var repassword = form.find('#repassword')
        var btn = form.find('[type="submit"]')

        Register.phoneResend.stop()
        $('.register-phone .resend').hide()

        phone.attr('readonly', true)

        username.check({ min: 6, max: 18, regx: { re: /^([a-zA-Z][a-zA-Z0-9_]+)|(\d+[a-zA-Z]+[a-zA-Z0-9_]*)$/ } })
        username.show()

        var regx = /^[\w\d\-\[\]{}|\\,.\/<>;:'"_`~!@#$%^&*()+= ]+$/
        password.check({ strip: false, min: 6, max: 18, regx: { re: regx }})
        repassword.check({ strip: false, equal: { element: password, message: texts.REPASSWORD_DIFF } })

        onBtnSubmit(form, 'submit.email.complete', btn, {
            url: urls.REGISTER_EMAIL,
            resetText: texts.REGISTER_COMPLETE,
            loadingText: texts.SENDING,
            completeText: texts.REGISTER_SUCCESS,
            check: function () { return username.check() && password.check() && repassword.check() },
            success: function () { Register.success() }
        })

        $K.hide()
    }

    Register.phoneResend = new Resend({
        form: '.register-phone-form',
        resend: '.register-phone .resend',
        url: urls.REGISTER_PHONE_SEND,
        check: function () { return $('.register-phone-form #phone').check() }
    })

    Register.phone = function () {
        if ($('.register-phone').length === 0) return
        Register.emailOff()
        Register.phoneOff()
        Register.phoneSend()
        $('.register-phone, .verify-code-box').show()
        $('.register-phone .use-email').on('click', function () {
            Register.email()
        })
    }

    Register.phoneOff = function () {
        $('.register-phone').hide()
        $('.register-phone-form').off('submit.phone.send')
        $('.register-phone-form').off('submit.phone.access')
        $('.register-phone-form').off('submit.phone.complete')
        $('.register-phone-form #phone').attr('readonly', false)
        $('.register-phone-form #authcode').hide()
        $('.register-phone-form #username').hide()
        $('.register-phone-form #password').hide()
        $('.register-phone .resend').hide()
        Register.phoneResend.stop()
        $K.hide()
    }

    Register.phoneSend = function () {
        var form = $('.register-phone-form')
        var phone = form.find('#phone')
        var btn = form.find('[type="submit"]')
        btn.text(texts.SEND_PHONE_CODE)
        phone.check({ regx: { re: /^1\d{10}$/ } })

        onBtnSubmit(form, 'submit.phone.send', btn, {
            url: urls.REGISTER_PHONE_SEND,
            resetText: texts.SEND_PHONE_CODE,
            loadingText: texts.SENDING,
            completeText: texts.NEXT,
            check: function () { return phone.check() },
            success: function () { Register.phoneAccess() },
            error: function (data) {
                if (data !== undefined && data.refresh === true) {
                    var src = $('.register-phone #verify_code_img').data('src') + '&t=' + Math.random()
                    $('.register-phone #verify_code_img').attr('src', src)
                }
            }
        })
    }

    Register.phoneAccess = function () {
        var form = $('.register-phone-form')
        var phone = form.find('#phone')
        var verifyCodeBox = form.find('.verify-code-box')
        var code = form.find('#authcode')
        var btn = form.find('[type="submit"]')

        Register.phoneResend.start()

        verifyCodeBox.hide()
        code.show()
        code.check({})
        phone.check({ regx: { re: /^1\d{10}$/ } })

        onBtnSubmit(form, 'submit.phone.access', btn, {
            url: urls.REGISTER_PHONE_ACCESS,
            resetText: texts.NEXT,
            loadingText: texts.ACCESSING,
            completeText: texts.REGISTER_COMPLETE,
            check: function () { return code.check() && phone.check() },
            success: function () { Register.phoneComplete() }
        })

        $K.hide()
    }

    Register.phoneComplete = function () {
        var form = $('.register-phone-form')
        var phone = form.find('#phone')
        var verifyCodeBox = form.find('.verify-code-box')
        var code = form.find('#authcode')
        var username = form.find('#username')
        var password = form.find('#password')
        var btn = form.find('[type="submit"]')

        Register.phoneResend.stop()
        $('.register-phone .resend').hide()

        phone.attr('readonly', true)
        verifyCodeBox.hide()
        code.hide()

        username.check({ min: 6, max: 18, regx: { re: /^([a-zA-Z][a-zA-Z0-9_]+)|(\d+[a-zA-Z]+[a-zA-Z0-9_]*)$/ } })
        username.show()

        var regx = /^[\w\d\-\[\]{}|\\,.\/<>;:'"_`~!@#$%^&*()+= ]+$/
        password.check({ strip: false, min: 6, max: 18, regx: { re: regx }})
        password.show()

        onBtnSubmit(form, 'submit.phone.complete', btn, {
            url: urls.REGISTER_PHONE,
            resetText: texts.REGISTER_COMPLETE,
            loadingText: texts.SENDING,
            completeText: texts.REGISTER_SUCCESS,
            check: function () { return username.check() && password.check() },
            success: function () { Register.success() }
        })

        $K.hide()
    }

    Register.success = function () {
        setTimeout(function () {
            window.location.href = urls.REGISTER_NEXT
        }, 100)
    }

    var ResetPassword = function (options) {
        if (options === 'phone') {
            ResetPassword.phone()
        } else {
            ResetPassword.email()
        }
    }

    ResetPassword.emailResend = new Resend({
        form: '.reset-password-email-form',
        resend: '.reset-password-email .resend',
        url: urls.RESET_PASSWORD_EMAIL_SEND,
        check: function () { return $('.reset-password-email-form #email').check() }
    })

    ResetPassword.email = function () {
        if ($('.reset-password-email').length > 0) {
            ResetPassword.emailOff()
            ResetPassword.phoneOff()
            ResetPassword.emailSend()
            $('.reset-password-email, .reset-password-email-form').show()
            $('.reset-password-email .use-phone').on('click', function () {
                ResetPassword.phone()
            })
        } else if ($('.reset-password-email-access').length > 0) {
            ResetPassword.emailComplete()
        } 
    }

    ResetPassword.emailOff = function () {
        ResetPassword.emailResend.stop()
        $('.reset-password-email').hide()
        $('.reset-password-email-form').off('submit.email.send')
        $('.email-access').html('')
        $K.hide()
    }

    ResetPassword.emailSend = function () {
        var form = $('.reset-password-email-form')
        var email = form.find('#email')
        var code = form.find('#verify_code')
        var btn = form.find('[type="submit"]')
        var regx = /^[\w\d]+[\d\w_.]+@([\d\w]+)\.([\d\w]+)(?:\.[\d\w]+)?$/
        code.check({})
        email.check({ max: 40, regx: { re: regx } })

        onBtnSubmit(form, 'submit.email.send', btn, {
            url: urls.RESET_PASSWORD_EMAIL_SEND,
            loadingText: texts.SENDING,
            completeText: texts.SEND_SUCCESS,
            check: function () { return email.check() && code.check() },
            success: function (data) { ResetPassword.emailAccess(email.val(), data.data.email_url) },
            error: function (data) {
                if (data !== undefined && data.refresh === true) {
                    var src = $('.reset-password-email #verify_code_img').data('src') + '&t=' + Math.random()
                    $('.reset-password-email #verify_code_img').attr('src', src)
                }
            }
        })

        $K.hide()
    }

    ResetPassword.emailAccess = function (email, url) {
        $('.reset-password-email-form').hide()
        $('.reset-password-email .email-access').html('')
        $('<div><p>重置密码邮件已发送, ' +
            '请<a href="${ url }" target="_blank">点击查收邮件</a>找回密码。</p>' +
            '没有收到邮件？请耐心等待，或者<a class="resend" href="javascript:;">重新发送</a></div>')
            .tmpl({ email: email, url: url })
            .appendTo('.reset-password-email .email-access')
        ResetPassword.emailResend.start()
        $K.hide()
    }

    ResetPassword.emailComplete = function () {
        var form = $('.reset-password-email-access-form')
        var phone = form.find('#phone')
        var code = form.find('#authcode')
        var password = form.find('#password')
        var repassword = form.find('#repassword')
        var btn = form.find('[type="submit"]')

        ResetPassword.phoneResend.stop()
        $('.reset-password-phone .resend').hide()

        phone.hide()
        code.hide()

        var regx = /^[\w\d\-\[\]{}|\\,.\/<>;:'"_`~!@#$%^&*()+= ]+$/
        password.check({ strip: false, min: 6, max: 18, regx: { re: regx }})
        password.show()
        repassword.check({ strip: false, equal: { element: password, message: texts.REPASSWORD_DIFF } })
        repassword.show()

        onBtnSubmit(form, 'submit.email.complete', btn, {
            url: urls.RESET_PASSWORD_EMAIL,
            resetText: texts.RESET_COMPLETE,
            loadingText: texts.SENDING,
            completeText: texts.RESET_SUCCESS,
            check: function () { return password.check() && repassword.check() },
            success: function () { ResetPassword.success() }
        })

        $K.hide()
    }

    ResetPassword.phoneResend = new Resend({
        form: '.reset-password-phone-form',
        resend: '.reset-password-phone .resend',
        url: urls.RESET_PASSWORD_PHONE_SEND,
        check: function () { return $('.reset-password-phone-form #phone').check() }
    })

    ResetPassword.phone = function () {
        if ($('.reset-password-phone').length === 0) return
        ResetPassword.emailOff()
        ResetPassword.phoneOff()
        ResetPassword.phoneSend()
        $('.reset-password-phone').show()
        $('.reset-password-phone .use-email').on('click', function () {
            ResetPassword.email()
        })
    }

    ResetPassword.phoneOff = function () {
        $('.reset-password-phone').hide()
        $('.reset-password-phone-form').off('submit.phone.send')
        $('.reset-password-phone-form').off('submit.phone.access')
        $('.reset-password-phone-form').off('submit.phone.complete')
        $('.reset-password-phone-form').show()
        $('.reset-password-phone-form #phone').show()
        $('.reset-password-phone-form #authcode').hide()
        $('.reset-password-phone-form #password').hide()
        $('.reset-password-phone-form #repassword').hide()
        $('.reset-password-phone .resend').hide()
        ResetPassword.phoneResend.stop()
        $K.hide()
    }

    ResetPassword.phoneSend = function () {
        var form = $('.reset-password-phone-form')
        var phone = form.find('#phone')
        var verifyCodeBox = form.find('.verify-code-box')
        var btn = form.find('[type="submit"]')
        btn.text(texts.SEND_PHONE_CODE)
        verifyCodeBox.show()
        phone.check({ regx: { re: /^1\d{10}$/ } })

        onBtnSubmit(form, 'submit.phone.send', btn, {
            url: urls.RESET_PASSWORD_PHONE_SEND,
            resetText: texts.SEND_PHONE_CODE, loadingText: texts.SENDING,
            completeText: texts.NEXT,
            check: function () { return phone.check() },
            success: function () { ResetPassword.phoneAccess() }
        })
    }

    ResetPassword.phoneAccess = function () {
        var form = $('.reset-password-phone-form')
        var phone = form.find('#phone')
        var code = form.find('#authcode')
        var btn = form.find('[type="submit"]')
        var verifyCodeBox = form.find('.verify-code-box')

        ResetPassword.phoneResend.start()

        verifyCodeBox.hide()
        code.show()
        code.check({})
        phone.check({ regx: { re: /^1\d{10}$/ } })

        onBtnSubmit(form, 'submit.phone.access', btn, {
            url: urls.RESET_PASSWORD_PHONE_ACCESS,
            resetText: texts.NEXT,
            loadingText: texts.ACCESSING,
            completeText: texts.RESET_COMPLETE,
            check: function () { return code.check() && phone.check() },
            success: function () { ResetPassword.phoneComplete() }
        })

        $K.hide()
    }

    ResetPassword.phoneComplete = function () {
        var form = $('.reset-password-phone-form')
        var phone = form.find('#phone')
        var code = form.find('#authcode')
        var password = form.find('#password')
        var repassword = form.find('#repassword')
        var btn = form.find('[type="submit"]')
        var verifyCodeBox = form.find('.verify-code-box')

        ResetPassword.phoneResend.stop()
        $('.reset-password-phone .resend').hide()

        phone.hide()
        verifyCodeBox.hide()
        code.hide()

        var regx = /^[\w\d\-\[\]{}|\\,.\/<>;:'"_`~!@#$%^&*()+= ]+$/
        password.check({ strip: false, min: 6, max: 18, regx: { re: regx }})
        password.show()
        repassword.check({ strip: false, equal: { element: password, message: texts.REPASSWORD_DIFF } })
        repassword.show()

        onBtnSubmit(form, 'submit.phone.complete', btn, {
            url: urls.RESET_PASSWORD_PHONE,
            resetText: texts.RESET_COMPLETE,
            loadingText: texts.SENDING,
            completeText: texts.RESET_SUCCESS,
            check: function () { return password.check() && repassword.check() },
            success: function () { ResetPassword.success() }
        })

        $K.hide()
    }

    ResetPassword.success = function () {
        setTimeout(function () {
            window.location.href = urls.RESET_PASSWORD_NEXT
        }, 100)
    }

    var users = {
        login: Login,
        register: Register,
        resetPassword: ResetPassword
    }

    $K.users = users
    window.$K = $K

    if (typeof(window.define) !== 'undefined') {
        window.define('users', ['jquery', 'cool'], function () {
            return users
        })
    } else {
        $(function () {
            users.login()
            users.register()
            users.resetPassword()
        })
    }

 } (jQuery)
