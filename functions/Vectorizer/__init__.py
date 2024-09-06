import azure.functions as func

from vectorizer_code.main import main as inner_main


def main(mytimer: func.TimerRequest) -> None:
    inner_main()
