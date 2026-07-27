# Deploy Backend-VITA lên Render

1. Tạo Web Service mới trên Render, trỏ vào repo `Backend-VITA`.
2. Build command: `pip install -r requirements.txt`
3. Start command: `python main.py` (hoặc `uvicorn main:app --host 0.0.0.0 --port $PORT` nếu main.py không tự đọc PORT — kiểm tra lại phần cuối main.py).
4. Vào tab **Environment**, thêm toàn bộ biến trong `.env.example` với giá trị thật của bạn (KHÔNG upload file `.env` lên Git).
   - `ALLOWED_ORIGINS` = domain GitHub Pages thật của bạn, ví dụ:
     `https://ninhs.github.io`
   - `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none` (bắt buộc vì frontend và backend khác domain).
5. Sau khi deploy xong, Render cho bạn 1 URL dạng `https://ten-app.onrender.com`.
   → Copy URL này, dán vào `UI/config.js` bên repo `Frontend-VITA` (biến `window.API_BASE_URL`).
6. Lưu ý: gói miễn phí của Render sẽ "ngủ" sau một thời gian không dùng, khi thức dậy
   `_auth_token` trong `main.py` sẽ được sinh lại → tất cả người dùng đang đăng nhập
   sẽ bị đăng xuất và cần đăng nhập lại. Đây là do thiết kế hiện tại (token toàn cục,
   không phải theo từng session) — không phải lỗi do việc tách domain.
