# 1. اختيار صورة بايثون خفيفة كقاعدة للمشروع
FROM python:3.9-slim

# 2. تحديد مكان العمل داخل الحاوية
WORKDIR /app

# 3. نسخ ملف المتطلبات أولاً (لتحسين سرعة البناء)
COPY requirements.txt .

# 4. تثبيت المكتبات
RUN pip install --no-cache-dir -r requirements.txt

# 5. نسخ باقي ملفات المشروع (HTML, CSS, JS, Python)
COPY . .

# 6. تحديد المنفذ الذي سيعمل عليه التطبيق (مثلاً 5000)
EXPOSE 5000

# 7. الأمر التشغيلي للمشروع
CMD ["python", "main.py"]