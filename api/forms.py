
async def simple_int(name, val):
    if val is None:
        return '{} is required'.format(name)
    elif not type(val) == int:
        return "{} is'n integer".format(name)
    return None

async def validate_create_message_form(form):
    from_user_id = form.get('userFromId')
    user_to_ids = form.get('UserToIds')
    body = form.get('body')

    result = await simple_int('from_user_id', int(from_user_id))
    if result: return result
    if not user_to_ids:
        return 'UserToIds is required'
    elif not type(user_to_ids) == list:
        return "UserToIds is'n list integers"
    if not body:
        return 'body is required'
    elif not type(body) == str:
        return "body is'n string type"

    return None

async def validate_list_message(form):
    user_id = int(form.get('user_id'))
    type_id = int(form.get('type'))
    result = await simple_int('user_id', user_id)
    if result: return result
    result = await simple_int('type', type_id)
    if result: return result
    return None

async def validate_view_message(form):
    user_id = int(form.get('user_id'))
    message_id = int(form.get('id'))
    result = await simple_int('user_id', user_id)
    if result: return result
    result = await simple_int('id', message_id)
    if result: return result
    return None

