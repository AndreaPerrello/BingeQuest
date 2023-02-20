import asyncio
from typing import Optional

from quart import Blueprint, jsonify, Response, websocket
from quart_events import EventBroker, EventBrokerAuthError
from quart_events.broker import logger, KeepAlive


class QuartEventBroker(EventBroker):

    def create_blueprint(self) -> Blueprint:
        """
        Generate the blueprint

        Returns:
            quart.Blueprint

        """
        blueprint = Blueprint("events", __name__)

        @blueprint.route("/auth")
        async def auth() -> Response:
            try:
                if self._auth_enabled:
                    await self.authorize_websocket()
                return jsonify(authorized=True)
            except EventBrokerAuthError as e:
                r = jsonify(authorized=False, error=str(e))
                r.status_code = 401
                return r
            except Exception as e:
                logger.exception(e)
                r = jsonify(authorized=False, error="an unknown error occurred")
                r.status_code = 400
                return r

        @blueprint.websocket("/ws")
        @blueprint.websocket("/ws/<namespace>")
        async def ws(namespace: Optional[str] = None) -> Response:
            _token = None
            if self._auth_enabled:
                try:
                    _token = await self.verify_auth()
                except EventBrokerAuthError as e:
                    await websocket.send_json({"event": "error", "message": str(e)})
                    return jsonify(error=str(e))
                except:
                    await websocket.send_json(
                        {"event": "error", "message": "not authorized"}
                    )
                    return jsonify(error="not authorized")

            # initial message
            await websocket.send_json({"event": "_open"})

            # enter subscriber loop
            async for data in self.subscribe():
                try:
                    """
                    KeepAlive:
                        * dummy event send at a regular interval to keep the socket from closing
                    Namespace:
                        * if a namespace is given but the "event" field is not, skip this event.
                        * if a namespace is given but does not match the "event" field, skip this event.
                    """
                    if self._auth_enabled and _token and self._token_is_expired(_token):
                        await websocket.send_json(
                            {"event": "_token_expire", "message": "token is expired"}
                        )
                        break
                    elif data is KeepAlive:
                        await websocket.send_json({"event": "_keepalive"})
                    elif namespace and (
                            data.get("event") is None
                            or not data["event"].startswith(namespace)
                    ):
                        continue
                    else:
                        await self._execute_callbacks(self._send_callbacks, data)
                        await websocket.send_json(data)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.exception(e)
                    logger.warning("ending subscriber loop")
                    break
            else:
                # final message
                await websocket.send_json({"event": "_close"})
            return jsonify(message="socket has ended")
        return blueprint
