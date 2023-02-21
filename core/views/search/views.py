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
        link = core.engine.get_link(media_hash)
        if link:
            return redirect(link)
        return redirect(url_for('movie_list'))
