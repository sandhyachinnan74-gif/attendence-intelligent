from locust import HttpUser, task, between

class WorkforceUser(HttpUser):
    wait_time = between(1, 2)
    token = None

    def on_start(self):
        # Authenticate as demo admin
        resp = self.client.post("/api/v1/auth/login", json={
            "email": "admin@attendai.com",
            "password": "Admin@123"
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    @task(4)
    def view_dashboard(self):
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.get("/api/v1/analytics/dashboard", headers=headers)

    @task(3)
    def search_employees(self):
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.get("/api/v1/employees?limit=25", headers=headers)

    @task(2)
    def view_attendance_records(self):
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.get("/api/v1/attendance?limit=50", headers=headers)

    @task(1)
    def ask_ai_assistant(self):
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.post("/api/v1/ai/chat", json={
                "content": "Show recent late arrivals"
            }, headers=headers)
