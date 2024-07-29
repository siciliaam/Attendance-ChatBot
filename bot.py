import logging
from telegram import InputFile
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import os
from collections import defaultdict
from dotenv import load_dotenv


load_dotenv()

bot_token = os.getenv('TOKEN_BOT')

# Fungsi untuk menangani perintah /start
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(f"Halo, {user.first_name}!\n"
                              "Berikut adalah Cara Penggunaan Bot.\n"
                              "/Absen - Kirimkan Keyword /Absen Untuk Melakukan Absen.\n" \
                              "Untuk Foto dengan Keterangan Lainnya, akan tetap dicatat, Silahkan masukan Keterangan berikut untuk Foto dengan Keterangan lainnya. 'Kunjungan','Dealing', 'EDK', 'Troubleshooting'.\n"
                              "/Kirim_Absensi - Kirimkan Keyword /Kirim_Absensi Untuk Mengirimkan Data Absensi Yang Telah Tercatat.\n"
                              )


# Fungsi untuk menangani perintah /absen
def absen(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Silahkan Kirim Foto Untuk Melakukan Absen, Masukan Keterangan ('Hadir', 'Izin', 'Lapangan');\nUntuk Foto dengan Keterangan Lainnya, akan tetap dicatat, Silahkan masukan Keterangan berikut untuk Foto dengan Keterangan lainnya.\n'Kunjungan','Dealing', 'EDK', 'Troubleshooting'.")


# Fungsi untuk menangani foto dan keterangan yang dikirim oleh pengguna
def handle_photo_with_keterangan(update: Update, context: CallbackContext):
    try:
        # Dapatkan objek foto dari pesan
        photo = update.message.photo[-1]

        # Dapatkan file_id foto untuk mengunduh foto
        file_id = photo.file_id

        # Dapatkan informasi pengirim dari update
        user_id = update.message.from_user.id
        username = update.message.from_user.first_name

        # Dapatkan tanggal dan waktu saat ini
        now = datetime.now()

        # Ubah format tanggal dan waktu
        tanggal = now.strftime("%Y-%m-%d")
        jam = now.strftime("%H:%M:%S")

        # Tambahkan label "Tanggal:" sebelum nilai tanggal
        tanggal_with_label = tanggal

        # Tambahkan label "Jam:" sebelum nilai jam
        jam_with_label = jam

        # Dapatkan keterangan teks dari pesan
        keterangan = update.message.caption if update.message.caption else " - "

        # Buat direktori dengan nama tanggal jika belum ada
        if not os.path.exists("data_absensi"):
            os.makedirs("data_absensi")

        # Unduh foto
        photo_file = context.bot.get_file(file_id)

        # Simpan foto dengan nama file yang berisi ID pengguna dan timestamp
        photo_path = f"{user_id}_{tanggal_with_label}.jpg"
        photo_file.download(photo_path)

        # Catat absensi dan keterangan ke dalam file txt
        with open("data_absensi.txt", "a") as file:
            file.write(f"{tanggal_with_label}-{jam_with_label} - {user_id} -  @{username} - {keterangan}\n")

        update.message.reply_text("Foto dan keterangan berhasil diterima dan absensi Anda telah dicatat.")
    except Exception as e:
        logging.error(f"Error saat menangani foto: {e}")
        update.message.reply_text("Terjadi kesalahan saat menangani foto dan keterangan. Mohon coba lagi nanti.")

def send_absensi_file(update: Update, context: CallbackContext):
    absensi_file = 'data_absensi.txt'
    if not os.path.exists(absensi_file):
        update.message.reply_text("File data absensi belum ada. Pastikan Anda telah mencatat absensi.")
        return
    data_per_hari = defaultdict(list)

    ## Baca file 'data_absensi.txt' dan proses datanya
    with open(absensi_file, 'r') as file:
        for line in file:
            if line.strip():
                tanggal = line.split('-')[0].strip().split()[-1]
                data_per_hari[tanggal].append(" || ".join(line.strip().split(" - ")))

    # Kirim file teks terpisah untuk setiap hari
    for tanggal, data in data_per_hari.items():
        # Buat file teks untuk hari ini dengan nama sesuai tanggal
        absensi_file_per_hari = f"data_absensi_{tanggal}.txt"
        with open(absensi_file_per_hari, 'w') as file:
            file.write("\n".join(data))

        # Kirim file teks sebagai dokumen
        with open(absensi_file_per_hari, 'rb') as file:
            update.message.reply_document(document=InputFile(file, filename=absensi_file_per_hari))

        # Hapus file teks sementara
        os.remove(absensi_file_per_hari)

def send_absensi_daily():
    updater = Updater(bot_token, use_context=True)
    context = updater.job_queue
    job = context.run_daily(send_absensi_file, time=datetime.time(0, 0))
    updater.start_polling()


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Tambahkan handler untuk tiap perintah
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo_with_keterangan))
    dispatcher.add_handler(CommandHandler("kirim_absensi", send_absensi_file))
    dispatcher.add_handler(CommandHandler("Absen", absen))


    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
