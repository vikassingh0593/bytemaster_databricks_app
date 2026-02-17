
# cfg with auth for Service Principal
sp_cfg = sdk.config.Config()

# request handler
async def query(user, request: gr.Request):

    # user's email
    email = request.headers.get("X-Forwarded-Email")

    # queries the database (or cache) to fetch user session using the SP
    user_session = get_user_session(sp_cfg, email)

    # user's access token
    user_token = request.headers.get("X-Forwarded-Access-Token")

    # queries the SQL Warehouse on behalf of the end-user
    result = query_warehouse(user_token)

    # save stats in user session
    save_user_session(sp_cfg, email)

    return result
