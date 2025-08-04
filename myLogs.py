from tools import get_time

class Mylogs():

    def _write_message(self, message, path):
        with open(path, "a+", encoding="utf-8") as file:
            file.write(message)



    def clear_logs(self):
        with open(self.error_log_path , "w") as f:
            f.write(get_time() + " -- " + self.session + "\n")

        with open(self.sending_log_path , "w") as f:
            f.write(get_time() + " -- " + self.session + "\n")

    def __init__(self, session):
        self.session = session
        self.sending_log_path = "logs/sending_logs.txt"
        self.error_log_path = "logs/error_logs.txt"
        self.clear_logs()
        self.enable = True

    def set_sending_log(self, id, first_name:str, is_new: bool):
        if self.enable:
            log = f"{get_time()} -- sending message to {'new' if is_new else 'leave'} user {first_name}|{id}\n"
            self._write_message(log, self.sending_log_path)

    def set_error_log(self, err, block_code):
        if self.enable:
            log = f"{get_time() } -- error occured in {block_code}: {err}\n"
            self._write_message(log, self.error_log_path)

    def get_error_logs(self) -> "IO":
        doc = open(self.error_log_path, 'rb')
        return doc

    def get_sending_logs(self) -> "IO":
        doc = open(self.sending_log_path , 'rb')
        return doc

    def disable_logs(self):
        self.enable = False

    def enable_logs(self):
        self.enable = True