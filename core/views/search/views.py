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
        kwargs = dict()
        if query:
            kwargs['title_prefix'] = f'{query} - '
        # Render the view
        return await render_template('search/index.html', result=result, **kwargs)

    @core.app.route('/deferred_execute', methods=['POST'])
    async def deferred_execute():
        try:
            # Decrypt secured data
            kwargs = security.decrypt_dict(request.args.get('d'))
            uid = kwargs.pop('u', None)
            if not uid:
                return core.response_bad_request('Unable to process the request.')
            return await core.engine.defer(uid, **kwargs)
        except Exception as e:
            return str(e), 500

    # @core.app.route('/proxy')
    # async def proxy():
    #     # Decrypt secured data
    #     d = request.args.get('d')
    #     if not d:
    #         return redirect(url_for('index'))
    #     try:
    #         kwargs = security.decrypt_dict(d)
    #     except:
    #         return redirect(url_for('index'))
    #     method = kwargs['method']
    #     url = urllib.parse.unquote(kwargs['url'])
    #     args = {k.title(): v for k, v in kwargs.items()}
    #     if method == 'get':
    #         response = scraping.get(url, headers=args)
    #     elif method == 'post':
    #         response = scraping.post(url, data=args)
    #     else:
    #         return core.response_bad_request('Unable to process the request.')
    #     soup = bs4.BeautifulSoup(response.text)
    #     base_tag = soup.new_tag('base')
    #     base_tag['href'] = url
    #     soup.html.head.append(base_tag)
    #     return str(soup), response.status_code
