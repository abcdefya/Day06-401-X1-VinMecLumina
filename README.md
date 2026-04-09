# VinMecLumina

## Hướng dẫn cài đặt nhanh

1. Clone repository về máy:

```bash
git clone <URL_REPO>
cd VinMecLumina
```

2. Tạo môi trường ảo với `uv`:

```bash
uv venv 
```

3. Kích hoạt môi trường ảo trong Git Bash:

```bash
source .venv/Scripts/activate
```

4. Cài đặt các thư viện từ `requirements.txt`:

```bash
uv pip install -r requirements.txt
```

5. Sau khi chạy xong, nếu cần tắt môi trường ảo:

```bash
deactivate
```

---

> Lưu ý: nếu dùng PowerShell thì lệnh kích hoạt sẽ là:
>
> ```powershell
> .\.venv\Scripts\Activate.ps1
> ```
