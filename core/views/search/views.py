from quart import redirect, url_for, render_template as quart_render_template, request

from iotech.microservice.web import spec

from ...engine import security


@spec.hookimpl(tryfirst=True)
def load_blueprints(core):
    def render_template(*args, title_prefix: str = None, **kwargs):
        title = "FlickWatch"
        if title_prefix:
            title = f"{title_prefix}{title}"
        return quart_render_template(*args, title=title, **kwargs)

    @core.app.route('/')
    async def index():
        return redirect(url_for('search'))

    @core.app.route('/search')
    @core.app.route('/search/')
    async def search():
        # Decrypt secured data
        data = security.decrypt_dict(request.args.get('d'))
        # If is a search by media hash
        media_hash = data.get('m')
        if media_hash:
            # Execute the media hash in the search engine and return the response
            media_response = await core.engine.execute_from_media_hash(media_hash)
            if media_response is None:
                return redirect(url_for('search', **request.view_args))
            return media_response
        # Canonical search by query
        query = request.args.get('q')
        uid = data.get('u')
        result = await core.engine.do_search(query, uid=uid)
        # Additional parameters for the view
        kwargs = {}
        if query:
            kwargs['title_prefix'] = f'{query} - '
        # Render the view
        return await render_template('search/results.html', result=result, **kwargs)

    @core.app.route('/proxy_post', methods=['POST'])
    async def proxy_post():
        try:
            params = await request.form
            url = params['url']
            data = {k.replace('data[', '').replace(']', ''): v for k, v in params.items() if k.startswith('data')}
            return await core.engine.proxy_post(url, data=data)
        except Exception as e:
            return str(e), 500
