# ---
# lambda-test: false
# ---
import fastapi
from starlette.responses import HTMLResponse, RedirectResponse

from modal import Stub, Image, asgi_app
from modal.functions import FunctionCall

stub = Stub("example-poll")

web_app = fastapi.FastAPI()


@stub.function(image=Image.debian_slim().pip_install("primefac"))
def factor_number(number):
    import primefac

    return list(primefac.primefac(number))  # could take a long time


@web_app.get("/")
async def index():
    return HTMLResponse(
        """
    <form method="get" action="/factors">
        Enter a number: <input name="number" />
        <input type="submit" value="Factorize!"/>
    </form>
    """
    )


@web_app.get("/factors")
async def web_submit(request: fastapi.Request, number: int):
    call = factor_number.spawn(
        number
    )  # returns a FunctionCall without waiting for result
    polling_url = request.url.replace(
        path="/result", query=f"function_id={call.object_id}"
    )
    return RedirectResponse(polling_url)


@web_app.get("/result")
async def web_poll(function_id: str):
    function_call = FunctionCall.from_id(function_id)
    try:
        result = function_call.get(timeout=0)
    except TimeoutError:
        result = "not ready"

    return result


@stub.function()
@asgi_app()
def fastapi_app():
    return web_app
