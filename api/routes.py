from api import views


def setup_routes(app):
    app.router.add_get('/', views.index, name='index')
    app.router.add_get('/ping', views.ping, name='ping')
    app.router.add_post('/api/message/create', views.send_message_post, name='create-message')
    app.router.add_get('/api/message/list', views.get_user_message_list, name='list-messages')
    app.router.add_get(r'/api/message/view/{id:\d+}', views.get_message_view, name='view-messages')
    app.router.add_put(r'/api/message/read/{id:\d+}', views.message_read_put, name='read-messages')
    app.router.add_delete(r'/api/message/delete/{id:\d+}', views.message_delete, name='delete-messages')


