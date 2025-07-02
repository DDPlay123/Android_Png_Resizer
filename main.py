import streamlit as st
from PIL import Image
import io
import zipfile

class AndroidImageResizer:
    density_map = {
        "ldpi": 0.75,
        "mdpi": 1.0,
        "hdpi": 1.5,
        "xhdpi": 2.0,
        "xxhdpi": 3.0,
        "xxxhdpi": 4.0
    }

    def __init__(self, base_density: str, target_densities: list[str]):
        self.base_density = base_density
        self.target_densities = target_densities
        self.base_scale = self.density_map[base_density]
        self.logs = []
        self.zip_buffer = io.BytesIO()

    def resize_images(self, files: list[io.BytesIO]):
        with zipfile.ZipFile(self.zip_buffer, "w") as zipf:
            for uploaded_file in files:
                try:
                    img = Image.open(uploaded_file)
                    base_width, base_height = img.size
                    self._log(f"🖼 處理圖片：{uploaded_file.name}（{base_width}x{base_height} px）")

                    for density in self.target_densities:
                        resized_img, path_in_zip = self._resize_image(img, uploaded_file.name, density)
                        img_byte_arr = io.BytesIO()
                        resized_img.save(img_byte_arr, format='PNG', optimize=True)
                        img_byte_arr.seek(0)

                        zipf.writestr(path_in_zip, img_byte_arr.read())
                        self._log(f"✅ {density:<7} → {resized_img.size[0]}x{resized_img.size[1]} px")

                except Exception as e:
                    self._log(f"❌ 錯誤處理圖片 {uploaded_file.name}：{e}")

    def _resize_image(self, img: Image.Image, filename: str, density: str):
        scale_ratio = self.density_map[density] / self.base_scale
        new_size = (int(img.width * scale_ratio), int(img.height * scale_ratio))
        resized_img = img.resize(new_size, Image.LANCZOS)
        path_in_zip = f"drawable-{density}/{filename}"
        return resized_img, path_in_zip

    def get_zip(self) -> bytes:
        self.zip_buffer.seek(0)
        return self.zip_buffer.read()

    def _log(self, message: str):
        self.logs.append(message)

    def show_logs(self):
        for log in self.logs:
            st.write(log)


class ResizerApp:
    def __init__(self):
        self.title = "📱 Android 多密度圖片轉換器"
        self.files = []
        self.base_density = "xhdpi"
        self.selected_densities = list(AndroidImageResizer.density_map.keys())

    def run(self):
        st.set_page_config(page_title=self.title)
        st.title(self.title)

        self.files = st.file_uploader("上傳 PNG 圖片（可多選）", type=["png"], accept_multiple_files=True)
        self.base_density = st.selectbox("原始圖片密度", list(AndroidImageResizer.density_map.keys()), index=3)
        self.selected_densities = st.multiselect(
            "選擇輸出密度", list(AndroidImageResizer.density_map.keys()), default=self.selected_densities
        )

        if st.button("🚀 開始轉換"):
            self.process_images()

    def process_images(self):
        if not self.files:
            st.error("請先上傳圖片")
            return
        if not self.selected_densities:
            st.error("請選擇至少一個輸出密度")
            return

        resizer = AndroidImageResizer(self.base_density, self.selected_densities)
        resizer.resize_images(self.files)
        resizer.show_logs()

        zip_bytes = resizer.get_zip()
        st.download_button(
            label="📦 下載所有轉換後圖片 (ZIP)",
            data=zip_bytes,
            file_name="resized_images.zip",
            mime="application/zip"
        )


if __name__ == "__main__":
    app = ResizerApp()
    app.run()
