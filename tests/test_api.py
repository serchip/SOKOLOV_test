from api import db

async def test_index_view(tables_and_data, client):
    resp = await client.get('/')
    assert resp.status == 200


async def test_create_message_form(tables_and_data, client):
    invalid_form ={"userFromId":1, "UserToIds": 1, "body": "Message test 333"}
    valid_form = {"userFromId":1, "UserToIds": [1, 2,3], "body": "Текст письма test"}

    resp = await client.post('/api/message/create', json=invalid_form)
    assert resp.status == 200
    assert {"success": False, "error": "UserToIds is'n list integers"} == await resp.json()

    resp = await client.post('/api/message/create', json=valid_form)
    assert resp.status == 200
    assert {"success": True} == await resp.json()

    session = client.server.app['db_session']
    sent_message_count = session.query(db.Message).filter(db.Message.from_user_id==1,
                                                    db.Message.type==db.Message.SENT
                                                    ).count()
    assert sent_message_count == 3
    inbox_message_count = session.query(db.Message).filter(db.Message.to_user_id==1,
                                                    db.Message.type==db.Message.INBOX
                                                    ).count()
    assert inbox_message_count == 1


async def test_message_list(tables_and_data, client):
    view_form = {
        'user_id': '1',
        'type': '0'
    }
    valid_form = {"userFromId":1, "UserToIds": [1, 2,3], "body": "Текст письма test"}
    resp = await client.post('/api/message/create', json=valid_form)
    assert resp.status == 200
    assert {"success": True} == await resp.json()

    #INBOX
    resp = await client.get('/api/message/list', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == True
    assert len(response_data['result']) == 1

    #SENT
    view_form = {
        'user_id': '1',
        'type': '1'
    }
    resp = await client.get('/api/message/list', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == True
    assert len(response_data['result']) == 3

async def test_message_view(tables_and_data, client):
    view_form = {
        'user_id': '1',
    }
    valid_form = {"userFromId":1, "UserToIds": [1, 2,3], "body": "Текст письма test"}
    resp = await client.post('/api/message/create', json=valid_form)
    assert resp.status == 200
    assert {"success": True} == await resp.json()

    resp = await client.get('/api/message/view/1', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == True
    assert response_data['result']['id'] == 1

    view_form = {
        'user_id': '3',
    }
    resp = await client.get('/api/message/view/1', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data == {}

async def test_message_read(tables_and_data, client):
    valid_form = {"userFromId":1, "UserToIds": [1, 2,3], "body": "Текст письма test"}
    resp = await client.post('/api/message/create', json=valid_form)
    assert resp.status == 200
    assert {"success": True} == await resp.json()

    view_form = {
        'user_id': '1',
    }
    resp = await client.get('/api/message/view/1', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == True
    assert response_data['result']['id'] == 1
    assert response_data['result']['read'] == False

    view_form = {
        'user_id': '1',
        'read': '1',
    }
    resp = await client.put('/api/message/read/1', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == True

    view_form = {
        'user_id': '1',
    }
    resp = await client.get('/api/message/view/1', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == True
    assert response_data['result']['id'] == 1
    assert response_data['result']['read'] == True

    view_form = {
        'user_id': '1',
        'read': '0',
    }
    resp = await client.put('/api/message/read/1', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == True

    view_form = {
        'user_id': '1',
    }
    resp = await client.get('/api/message/view/1', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == True
    assert response_data['result']['id'] == 1
    assert response_data['result']['read'] == False


async def test_message_delete(tables_and_data, client):
    valid_form = {"userFromId":1, "UserToIds": [1,2,3], "body": "Текст письма test"}
    resp = await client.post('/api/message/create', json=valid_form)
    assert resp.status == 200
    assert {"success": True} == await resp.json()
    session = client.server.app['db_session']
    mess_count = session.query(db.Message).count()
    assert mess_count == 6

    view_form = {
        'user_id': '2',
    }
    resp = await client.delete('/api/message/delete/6', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == False
    assert response_data['error'] == 'Message not found'

    mess_count = session.query(db.Message).filter(db.Message.id==6).count()
    assert mess_count == 1

    view_form = {
        'user_id': '1',
    }
    resp = await client.delete('/api/message/delete/6', params=view_form)
    assert resp.status == 200
    response_data = await resp.json()
    assert response_data['success'] == True

    mess_count = session.query(db.Message).filter(db.Message.id==6).count()
    assert mess_count == 0

