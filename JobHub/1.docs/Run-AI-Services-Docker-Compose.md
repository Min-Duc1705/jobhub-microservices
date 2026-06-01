# Chạy 2 AI Service bằng Docker Compose

Tài liệu này dùng cho project `Backend/docker-compose.yml` sau khi `CVIntelligenceService` và `DataAnalyticsService` đã được đưa vào cùng Compose project `backend`.

## 1. Chuẩn bị

Mở Docker Desktop trước, sau đó mở PowerShell tại thư mục backend:

```powershell
cd T:\TryHard_IT_Project\Final\Backend
```

Nếu trước đó bạn từng chạy 2 AI service bằng `docker run`, hãy xóa container standalone để Compose quản lý lại:

```powershell
docker stop jobhub_cvintelligence jobhub_dataanalytics
docker rm jobhub_cvintelligence jobhub_dataanalytics
```

Nếu lệnh báo container không tồn tại thì bỏ qua.

## 2. Build image tất cả service trong dự án

Lệnh này build toàn bộ service có Dockerfile trong `Backend/JobHub`:

```powershell
docker compose build authservice jobservice companyservice profileservice resumeservice notificationservice apigateway cvintelligenceservice dataanalyticsservice
```

Các image được tạo:

```text
jobhub-authservice:latest
jobhub-jobservice:latest
jobhub-companyservice:latest
jobhub-profileservice:latest
jobhub-resumeservice:latest
jobhub-notificationservice:latest
jobhub-apigateway:latest
jobhub-cvintelligenceservice:latest
jobhub-dataanalyticsservice:latest
```

## 3. Chạy riêng 2 AI service

Chạy MongoDB, RabbitMQ và 2 AI service trong cùng Compose project:

```powershell
docker compose up -d mongodb rabbitmq cvintelligenceservice dataanalyticsservice
```

Kiểm tra container:

```powershell
docker compose ps
```

Trong Docker Desktop, các container `jobhub_cvintelligence` và `jobhub_dataanalytics` sẽ nằm trong nhóm `backend`.

## 4. Kiểm tra API

Health check:

```powershell
Invoke-RestMethod http://localhost:5006/health
Invoke-RestMethod http://localhost:5007/health
```

Swagger/FastAPI docs:

```text
http://localhost:5006/docs
http://localhost:5007/docs
```

Endpoint chính:

```text
POST http://localhost:5006/api/v1/cv/score
POST http://localhost:5006/api/v1/cv/score/batch
POST http://localhost:5007/api/v1/analytics/salary/predict
POST http://localhost:5007/api/v1/analytics/trend
```

## 5. Logs và dừng service

Xem logs:

```powershell
docker compose logs -f cvintelligenceservice
docker compose logs -f dataanalyticsservice
```

Dừng 2 AI service:

```powershell
docker compose stop cvintelligenceservice dataanalyticsservice
```

Dừng và xóa container của 2 AI service:

```powershell
docker compose rm -sf cvintelligenceservice dataanalyticsservice
```

## Ghi chú cấu hình

- Khi chạy trong Docker Compose, `MONGO_URL` dùng host `mongodb`, không dùng `localhost`.
- Khi chạy trong Docker Compose, `RABBITMQ_URL` dùng host `rabbitmq`, không dùng `localhost`.
- `.env` vẫn được đọc để lấy các biến khác như `GEMINI_API_KEY`, `SBERT_MODEL`, `MODEL_PATH`.
- Các .NET service đã được khai báo trong Compose với profile `app`, nên không tự bật khi chỉ chạy 2 AI service.
- Nếu muốn chạy full backend gồm cả .NET services và API Gateway:

```powershell
docker compose --profile app up -d --build
```
