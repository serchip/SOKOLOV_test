from aiohttp import web
from sqlalchemy import desc, or_, and_

from api import db
from api import forms


def redirect(router, route_name):
    location = router[route_name].url_for()
    return web.HTTPFound(location)

async def index(request):
    return web.HTTPFound('/api/doc')

async def ping(request):
    """
    ---
    description: ping service
    tags:
    - ping
    produces:
    - text/plain
    responses:
    "200":
    description: successful operation.
    "405":
    description: invalid HTTP Method
    """
    return web.Response(text="pong")

async def send_message_post(request):
    """
    ---
    description: Send Message from User to Users.
    tags:
    - "message"
    produces:
    - "application/json"
    parameters:
      - name: "body"
        in: body
        description: '{"userFromId":1, "UserToIds": [1,2,3], "body": "Текст письма"} '
        required: true
        type: "string"
    responses:
      "200":
        description: Success
      "405":
        description: invalid HTTP Method
    """
    response_data = {}
    if request.method == 'POST':
        data = await request.json()
        error = await forms.validate_create_message_form(data)

        if error:
            response_data = {'success': False, 'error': error}
        else:
            session = request.app['db_session']
            current_user = session.query(db.Users).filter(db.Users.id==int(data['userFromId'])).one_or_none()
            users_to  = session.query(db.Users).filter(db.Users.id.in_(data['UserToIds'])).all()
            for to_user in users_to:
                message = db.Message(body=data['body'],  from_user_id=current_user.id,
                                      to_user_id=to_user.id, type=db.Message.INBOX)
                session.add(message)
                message = db.Message(body=data['body'],  from_user_id=current_user.id,
                                      to_user_id=to_user.id, type=db.Message.SENT)
                session.add(message)
            session.commit()
            response_data = {'success': True}
    return web.json_response(response_data)


async def get_user_message_list(request):
    """
    ---
    description: User List Messages filter by type.
    tags:
    - "message"
    produces:
    - "application/json"
    parameters:
      - name: "user_id"
        in: query
        description: 'user_id that needs to be fetched'
        required: true
        type: "interger"
      - name: "type"
        in: query
        description: 'inbox=0 or sent=1'
        required: true
        type: "integer"
        enum:
        - "0"
        - "1"
    responses:
      "200":
        description: List
      "405":
        description: invalid HTTP Method
    """
    response_data = {}
    if request.method == 'GET':
        data = request.rel_url.query.copy()
        error = await forms.validate_list_message(data)

        if error:
            response_data = {'success': False, 'error': error}
        else:
            session = request.app['db_session']
            if int(data['type'])==db.Message.SENT:
                message_list  = session.query(db.Message).filter(db.Message.from_user_id==int(data['user_id']),
                                                                 db.Message.type==db.Message.SENT
                                                                 ).order_by(desc(db.Message.timestamp)).all()
            else:
                message_list = session.query(db.Message).filter(db.Message.to_user_id == int(data['user_id']),
                                                                db.Message.type == db.Message.INBOX
                                                                ).order_by(desc(db.Message.timestamp)).all()
            response_data = {'result': [message.as_dict() for message in message_list]}
            response_data.update({'success': True})
    return web.json_response(response_data)


async def get_message_view(request):
    """
    ---
    description: User View Messages filter by id and user_id.
    tags:
    - "message"
    produces:
    - "application/json"
    parameters:
      - name: "user_id"
        in: query
        description: 'user_id that needs to be owner or recipient'
        required: true
        type: "interger"
      - name: "id"
        in: path
        description: 'massage pk'
        required: true
        type: "integer"
    responses:
      "200":
        description: View Message
      "405":
        description: invalid HTTP Method
    """
    response_data = {}
    if request.method == 'GET':
        data = request.rel_url.query.copy()
        data['id'] = request.match_info.get('id')
        error = await forms.validate_view_message(data)

        if error:
            response_data = {'success': False, 'error': error}
        else:
            session = request.app['db_session']
            message  = session.query(db.Message).filter(db.Message.id==int(data['id']))\
                .filter(or_(db.Message.from_user_id==int(data['user_id']),
                            db.Message.to_user_id == int(data['user_id'])
                            )
                        ).one_or_none()
            if message:
                response_data = {'result': message.as_dict()}
                response_data.update({'success': True})
    return web.json_response(response_data)


async def message_read_put(request):
    """
    ---
    description: Update Message flag read (user_id owner or recipient).
    tags:
    - "message"
    produces:
    - "application/json"
    parameters:
      - name: "user_id"
        in: query
        description: 'user_id that needs to be owner or recipient'
        required: true
        type: "interger"
      - name: "id"
        in: path
        description: 'massage pk'
        required: true
        type: "integer"
      - name: "read"
        in: query
        description: 'not read=0 or read=1, default update read'
        required: true
        type: "integer"
        enum:
        - "1"
        - "0"
    responses:
      "200":
        description: View Message
      "405":
        description: invalid HTTP Method
    """
    response_data = {}
    if request.method == 'PUT':
        data = request.rel_url.query.copy()
        data['id'] = request.match_info.get('id')
        error = await forms.validate_view_message(data)
        read = True if int(data.get('read', 1)) == 1 else False
        if error:
            response_data = {'success': False, 'error': error}
        else:
            session = request.app['db_session']
            session.query(db.Message).filter(db.Message.id==int(data['id']))\
                .filter(or_(and_(db.Message.from_user_id==int(data['user_id']), db.Message.type == db.Message.SENT),
                            and_(db.Message.to_user_id == int(data['user_id']), db.Message.type == db.Message.INBOX)
                            )
                        ) \
                .update({"read": read})
            session.commit()
            response_data = {'success': True}

    return web.json_response(response_data)

async def message_delete(request):
    """
    ---
    description: Delete Message (user_id owner or recipient).
    tags:
    - "message"
    produces:
    - "application/json"
    parameters:
      - name: "user_id"
        in: query
        description: 'user_id that needs to be owner or recipient'
        required: true
        type: "interger"
      - name: "id"
        in: path
        description: 'massage pk for delete'
        required: true
        type: "integer"
    responses:
      "200":
        description: Delete Message
      "405":
        description: invalid HTTP Method
    """
    response_data = {}
    if request.method == 'DELETE':
        data = request.rel_url.query.copy()
        data['id'] = request.match_info.get('id')
        error = await forms.validate_view_message(data)
        if error:
            response_data = {'success': False, 'error': error}
        else:
            session = request.app['db_session']
            message = session.query(db.Message).filter(db.Message.id==int(data['id']))\
                .filter(or_(and_(db.Message.from_user_id==int(data['user_id']), db.Message.type == db.Message.SENT),
                            and_(db.Message.to_user_id == int(data['user_id']), db.Message.type == db.Message.INBOX)
                            )
                        ) \
                .one_or_none()
            if not message:
                response_data = {'success': False, 'error': 'Message not found'}
            else:
                session.query(db.Message).filter(db.Message.id == message.id).delete()
                session.commit()
                response_data = {'success': True}

    return web.json_response(response_data)

