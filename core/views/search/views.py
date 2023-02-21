from quart import redirect, url_for, render_template as quart_render_template, request

from iotech.microservice.web import spec


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

    # Devices

    @core.app.route('/search/')
    async def search():
        q = request.args.get('q')
        result = await core.engine.execute_search(q)
        kwargs = {}
        if q:
            kwargs['title_prefix'] = f'{q} - '
        return await render_template('movie/grid.html', result=result, **kwargs)

    @core.app.route('/search/<media_hash>/')
    async def search_link(media_hash: str):
        return_value = await core.engine.execute_from_hash(media_hash)
        if return_value is not None:
            return return_value
        return redirect(url_for('search', **request.view_args))

    @core.app.route('/proxy_post', methods=['POST'])
    async def proxy_post():
        try:
            params = await request.form
            url = params['url']
            data = {k.replace('data[', '').replace(']', ''): v for k, v in params.items() if k.startswith('data')}
            return await core.engine.proxy_post(url, data=data)
        except Exception as e:
            return str(e), 500
