class NotificationService:
    @staticmethod
    def send(title: str, message: str):
        print(f"[NOTIFICATION] {title}: {message}")
