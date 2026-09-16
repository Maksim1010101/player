"""Главный модуль запуска аудио плейера с GUI."""

import json
import tkinter as tk
from importlib import import_module
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from typing import Dict, Optional
from player import PlayList, Composition


class PlayerGUI:  # pylint: disable=too-many-instance-attributes
    """Класс управления графическим интерфейсом плейера."""

    def __init__(self, root_window: tk.Tk) -> None:
        """Инициализация главного окна и компонентов UI."""
        self.root: tk.Tk = root_window
        self.root.title("Плейер")
        self.root.geometry("650x450")

        # Хранилище плейлистов: {Имя_плейлиста: Объект_PlayList}
        self.playlists: Dict[str, PlayList] = {}
        self.current_playlist: Optional[PlayList] = None
        self._pygame = None
        self._playback_active = False
        self._playback_paused = False
        self._storage_path = Path(__file__).with_name("playlists.json")

        self._build_ui()
        self._load_playlists()
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _load_playlists(self) -> None:
        """Загрузить плейлисты и композиции из файла."""
        if not self._storage_path.exists():
            return
        try:
            with self._storage_path.open("r", encoding="utf-8") as storage:
                saved_playlists = json.load(storage)
            for saved_playlist in saved_playlists:
                playlist = PlayList(saved_playlist["name"])
                for saved_track in saved_playlist.get("tracks", []):
                    playlist.append(
                        Composition(
                            saved_track["title"],
                            saved_track["artist"],
                            saved_track.get("file_path"),
                        )
                    )
                self.playlists[playlist.name] = playlist
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            messagebox.showwarning(
                "Ошибка загрузки",
                f"Не удалось загрузить сохранённые данные:\n{error}",
            )
            return
        self._update_playlist_ui()
        if self.playlists:
            first_name = next(iter(self.playlists))
            self.current_playlist = self.playlists[first_name]
            self.playlist_box.selection_set(0)
            self.track_label.config(text=f"Треки плейлиста: {first_name}")
            self._update_tracks_ui()

    def _save_playlists(self) -> None:
        """Сохранить плейлисты и композиции в файл."""
        saved_playlists = []
        for playlist in self.playlists.values():
            saved_playlists.append(
                {
                    "name": playlist.name,
                    "tracks": [
                        {
                            "title": track.data.title,
                            "artist": track.data.artist,
                            "file_path": track.data.file_path,
                        }
                        for track in playlist
                    ],
                }
            )
        try:
            with self._storage_path.open("w", encoding="utf-8") as storage:
                json.dump(saved_playlists, storage, ensure_ascii=False, indent=2)
        except OSError as error:
            messagebox.showerror(
                "Ошибка сохранения",
                f"Не удалось сохранить данные:\n{error}",
            )

    def _close(self) -> None:
        """Сохранить данные перед закрытием приложения."""
        self._save_playlists()
        self.root.destroy()

    def _build_ui(self) -> None:
        """Создание виджетов."""
        # --- Левая панель: Плейлисты ---
        left_frame = tk.Frame(self.root, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_frame, text="Плейлисты", font=("Arial", 12, "bold")).pack()
        self.playlist_box = tk.Listbox(left_frame, width=20, height=15)
        self.playlist_box.pack(pady=5)
        self.playlist_box.bind("<<ListboxSelect>>", self._on_playlist_select)

        tk.Button(left_frame, text="Создать плейлист", command=self.create_playlist, width=18).pack(pady=2)
        tk.Button(left_frame, text="Удалить плейлист", command=self.delete_playlist, width=18).pack(pady=2)

        # --- Правая панель: Треки и Управление ---
        right_frame = tk.Frame(self.root, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.track_label = tk.Label(right_frame, text="Плейлист не выбран", font=("Arial", 12, "bold"))
        self.track_label.pack()

        self.track_box = tk.Listbox(right_frame, height=12)
        self.track_box.pack(fill=tk.BOTH, expand=True, pady=5)

        # Кнопки работы с треками
        track_btn_frame = tk.Frame(right_frame)
        track_btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(track_btn_frame, text="Добавить трек", command=self.add_track).pack(side=tk.LEFT, padx=2)
        tk.Button(track_btn_frame, text="Удалить трек", command=self.delete_track).pack(side=tk.LEFT, padx=2)
        tk.Button(track_btn_frame, text="Вверх", command=lambda: self.move_track(-1)).pack(side=tk.LEFT, padx=2)
        tk.Button(track_btn_frame, text="Вниз", command=lambda: self.move_track(1)).pack(side=tk.LEFT, padx=2)

        # Панель плеера
        player_frame = tk.LabelFrame(right_frame, text="Воспроизведение", pady=10, padx=10)
        player_frame.pack(fill=tk.X, pady=10)

        self.now_playing_label = tk.Label(player_frame, text="Сейчас играет: -", fg="green", font=("Arial", 10, "italic"))
        self.now_playing_label.pack(pady=5)

        control_frame = tk.Frame(player_frame)
        control_frame.pack()

        tk.Button(control_frame, text="⏮ Пред", command=self.prev_track, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="▶ Старт", command=self.play_track, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="⏭ След", command=self.next_track, width=8).pack(side=tk.LEFT, padx=5)

    def create_playlist(self) -> None:
        """Создание нового плейлиста"""
        name = simpledialog.askstring("Новый плейлист", "Введите имя плейлиста:")
        if name:
            name = name.strip()
            if name in self.playlists:
                messagebox.showwarning("Ошибка", "Плейлист с таким именем уже существует.")
                return
            playlist = PlayList(name)
            self.playlists[name] = playlist
            self.current_playlist = playlist
            self._update_playlist_ui()
            playlist_index = self.playlist_box.get(0, tk.END).index(name)
            self.playlist_box.selection_clear(0, tk.END)
            self.playlist_box.selection_set(playlist_index)
            self.track_label.config(text=f"Треки плейлиста: {name}")
            self._update_tracks_ui()
            self._update_now_playing()
            self._save_playlists()

    def delete_playlist(self) -> None:
        """Удаление выбранного плейлиста (Пункт 2)."""
        selected = self.playlist_box.curselection()
        if not selected:
            return
        name = self.playlist_box.get(selected[0])  # ИСПРАВЛЕНО: берем первый элемент кортежа
        del self.playlists[name]
        if self.current_playlist and self.current_playlist.name == name:
            self.current_playlist = None
            self.now_playing_label.config(text="Сейчас играет: -")
        self._update_playlist_ui()
        self._update_tracks_ui()
        self._save_playlists()

    def add_track(self) -> None:
        """Добавить композицию в текущий плейлист (Пункт 3)."""
        selected = self.playlist_box.curselection()
        if selected:
            playlist_name = self.playlist_box.get(selected[0])
            self.current_playlist = self.playlists.get(playlist_name)
        if self.current_playlist is None:
            messagebox.showwarning("Ошибка", "Сначала выберите или создайте плейлист.")
            return
        artist = simpledialog.askstring("Добавить трек", "Введите исполнителя:")
        title = simpledialog.askstring("Добавить трек", "Введите название трека:")
        if artist and title:
            file_path = filedialog.askopenfilename(
                title="Выберите аудиофайл",
                filetypes=(
                    ("Аудиофайлы", "*.mp3 *.wav *.ogg"),
                    ("Все файлы", "*.*"),
                ),
            )
            comp = Composition(title.strip(), artist.strip(), file_path or None)
            self.current_playlist.append(comp)
            self._update_tracks_ui()
            self._save_playlists()

    def delete_track(self) -> None:
        """Удаление композиции из плейлиста (Пункт 4)."""
        if not self.current_playlist:
            return
        selected = self.track_box.curselection()
        if not selected:
            return
        idx = selected[0]  # ИСПРАВЛЕНО: преобразуем кортеж в числовой индекс
        comp_to_remove = self.current_playlist[idx]

        if self.current_playlist.current == comp_to_remove:
            self.current_playlist.next_track()
            if len(self.current_playlist) <= 1:
                self.now_playing_label.config(text="Сейчас играет: -")

        self.current_playlist.remove(comp_to_remove)
        self._update_tracks_ui()
        self._update_now_playing()
        self._save_playlists()

    def move_track(self, direction: int) -> None:
        """Перемещение композиции Вверх/Вниз (Пункт 5)."""
        if not self.current_playlist:
            return
        selected = self.track_box.curselection()
        if not selected:
            return
        idx = selected[0]  # ИСПРАВЛЕНО
        new_idx = idx + direction

        if 0 <= new_idx < len(self.current_playlist):
            self.current_playlist.move_composition(idx, new_idx)
            self._update_tracks_ui()
            self.track_box.selection_clear(0, tk.END)
            self.track_box.selection_set(new_idx)
            self._save_playlists()

    def play_track(self) -> None:
        """Проигрывание выбранной музыкальной композиции (Пункт 6)."""
        if not self.current_playlist or len(self.current_playlist) == 0:
            return
        selected = self.track_box.curselection()
        selected_track = self.current_playlist[selected[0]] if selected else None
        if self._pygame is not None and self._playback_paused:
            if selected_track is None or selected_track == self.current_playlist.current:
                self._pygame.mixer.music.unpause()
                self._playback_paused = False
                self._playback_active = True
                self._update_now_playing()
                return
            self._stop_audio()
        if self._playback_active and self._pygame is not None:
            if selected_track is None or selected_track == self.current_playlist.current:
                self._pause_audio()
                return
            self._stop_audio()
        if selected:
            idx = selected[0]  # ИСПРАВЛЕНО
            comp = self.current_playlist[idx]
            self.current_playlist.play_all(comp)
        else:
            if not self.current_playlist.current:
                first_comp = self.current_playlist[0]
                self.current_playlist.play_all(first_comp)
        self._start_audio()
        self._update_now_playing()

    def next_track(self) -> None:
        """Запуск последующей композиции (Пункт 8, 9)."""
        if self.current_playlist:
            self.current_playlist.next_track()
            self._select_current_track()
            self._start_audio()
            self._update_now_playing()

    def prev_track(self) -> None:
        """Запуск предыдущей музыкальной композиции (Пункт 7)."""
        if self.current_playlist:
            self.current_playlist.previous_track()
            self._select_current_track()
            self._start_audio()
            self._update_now_playing()

    def _select_current_track(self) -> None:
        """Выделить в интерфейсе композицию, выбранную кнопкой навигации."""
        if self.current_playlist is None or self.current_playlist.current is None:
            return
        for index, track in enumerate(self.current_playlist):
            if track.data is self.current_playlist.current:
                self.track_box.selection_clear(0, tk.END)
                self.track_box.selection_set(index)
                self.track_box.see(index)
                return

    def _start_audio(self) -> None:
        """Запустить текущий файл и запланировать переход после его окончания."""
        if self.current_playlist is None or self.current_playlist.current is None:
            return
        composition = self.current_playlist.current
        if not composition.file_path:
            self._playback_active = False
            self._playback_paused = False
            return
        if self._pygame is None:
            try:
                self._pygame = import_module("pygame")
            except ImportError:
                messagebox.showwarning(
                    "Воспроизведение недоступно",
                    "Установите пакет pygame для проигрывания аудиофайлов.",
                )
                return
            self._pygame.mixer.init()
        self._pygame.mixer.music.load(composition.file_path)
        self._pygame.mixer.music.play()
        self._playback_active = True
        self._playback_paused = False
        self.root.after(250, self._check_audio_end)

    def _pause_audio(self) -> None:
        """Приостановить воспроизведение, сохранив текущую позицию."""
        self._playback_active = False
        if self._pygame is not None:
            self._pygame.mixer.music.pause()
        self._playback_paused = True

    def _stop_audio(self) -> None:
        """Остановить текущий аудиофайл при смене композиции или плейлиста."""
        self._playback_active = False
        self._playback_paused = False
        if self._pygame is not None:
            self._pygame.mixer.music.stop()

    def _check_audio_end(self) -> None:
        """Перейти к следующему треку после окончания текущего."""
        if not self._playback_active:
            return
        if self._pygame is None or not self._pygame.mixer.music.get_busy():
            self._playback_active = False
            if self.current_playlist is not None:
                self.current_playlist.next_track()
                self._update_now_playing()
                self._start_audio()
            return
        self.root.after(250, self._check_audio_end)

    def _on_playlist_select(self, event: tk.Event) -> None:
        """Обработчик выбора плейлиста в левом окне."""
        _ = event
        selected = self.playlist_box.curselection()
        if selected:
            name = self.playlist_box.get(selected[0])  # ИСПРАВЛЕНО: извлекаем строку по числовому индексу
            self._stop_audio()
            self.current_playlist = self.playlists[name]
            self.track_label.config(text=f"Треки плейлиста: {name}")
            self._update_tracks_ui()
            self._update_now_playing()

    def _update_playlist_ui(self) -> None:
        """Синхронизация списка плейлистов на экране."""
        self.playlist_box.delete(0, tk.END)
        for name in self.playlists:
            self.playlist_box.insert(tk.END, name)

    def _update_tracks_ui(self) -> None:
        """Синхронизация списка треков на экране."""
        self.track_box.delete(0, tk.END)
        if self.current_playlist:
            for track in self.current_playlist:
                self.track_box.insert(tk.END, str(track.data))

    def _update_now_playing(self) -> None:
        """Обновление строки текущего статуса плейера."""
        if self.current_playlist and self.current_playlist.current:
            self.now_playing_label.config(text=f"Сейчас играет: {self.current_playlist.current}")
        else:
            self.now_playing_label.config(text="Сейчас играет: -")


if __name__ == "__main__":
    root = tk.Tk()
    app = PlayerGUI(root)
    root.mainloop()
