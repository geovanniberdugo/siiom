import views

from django.conf import settings
from django.contrib import admin
from django.urls import include, re_path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView, TemplateView
from miembros.views import login, logout, administracion
from miembros import forms as miembros_forms

admin.autodiscover()
RedirectView.permanent = True

pwaurls = [
    re_path(r'^feed/$', TemplateView.as_view(template_name='feed/feed.html')),
    re_path(r'^offline$', TemplateView.as_view(template_name='offline.html')),
    re_path(r'^manifest.json$', TemplateView.as_view(template_name='manifest.json')),
    re_path(r'^serviceworker.js$', TemplateView.as_view(
        template_name='serviceworker.js',
        content_type='application/javascript'
    )),
]

urlpatterns = pwaurls + [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^$', RedirectView.as_view(url="/iniciar_sesion/")),
    re_path(r'^iniciar_sesion/$', login, name="inicio"),
    re_path(r'^salir/$', logout, name='logout'),
    re_path(r'^administracion/$', administracion, name="administracion"),
    re_path(r'^miembro/', include("miembros.urls", namespace='miembros')),
    re_path(r'^grupo/', include("grupos.urls", namespace='grupos')),
    re_path(r'^reportes/', include("reportes.urls", namespace='reportes')),
    re_path(r'^encuentro/', include("encuentros.urls", namespace='encuentros')),
    re_path(r'^consolidacion/', include("consolidacion.urls", namespace="consolidacion")),
    re_path(r'^instituto/', include("instituto.urls", namespace="instituto")),
    re_path(r'^common/', include("common.urls", namespace="common")),
    re_path(r'^dont_have_permissions/$', views.without_perms, name="sin_permiso"),

    re_path(r'^organizacional/', include("organizacional.urls", namespace="organizacional")),
    re_path(r'^requisiciones/', include("compras.urls", namespace="compras")),
    re_path(r'^sgd/', include("gestion_documental.urls", namespace="sgd")),
    re_path(r'^pqr/', include("pqr.urls", namespace="pqr")),

    re_path(r'^buscar/(grupo|miembro)/$', views.buscar, name='buscar'),
    re_path(
        r'^recuperar_contrasena/$', auth_views.PasswordResetView.as_view(
            subject_template_name='miembros/contrasena/email_subject.html',
            template_name='miembros/contrasena/password_reset_form.html',
            email_template_name='miembros/contrasena/email_body.html',
            form_class=miembros_forms.PasswordResetForm,
        ),
        name="recuperar_contrasena"
    ),
    re_path(
        r'^recuperar_contrasena/enviado/$', auth_views.PasswordResetDoneView.as_view(template_name='miembros/contrasena/password_reset_done.html'),
        name="password_reset_done"),
    re_path(
        r'^resetear_contrasena/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='miembros/contrasena/password_reset_confirm.html',
            form_class=miembros_forms.SetPasswordForm,
        ),
        name="password_reset_confirm"
    ),
    re_path(
        r'^resetear_contrasena/done/$',
        auth_views.PasswordResetCompleteView.as_view(template_name='miembros/contrasena/password_reset_complete.html'),
        name="password_reset_complete"
    ),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
