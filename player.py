"""Модели композиций и плейлистов."""

from typing import Optional

from linked_list import LinkedList, LinkedListItem


class Composition:
    """Музыкальная композиция."""

    def __init__(self, title: str, artist: str, file_path: Optional[str] = None) -> None:
        """Создать композицию."""
        self.title = title
        self.artist = artist
        self.file_path = file_path

    def __str__(self) -> str:
        """Вернуть отображаемое имя композиции."""
        return f"{self.artist} - {self.title}"

    def __eq__(self, other: object) -> bool:
        """Сравнить композиции по исполнителю и названию."""
        if not isinstance(other, Composition):
            return NotImplemented
        return self.title == other.title and self.artist == other.artist


class PlayList(LinkedList):
    """Плейлист, построенный на кольцевом двусвязном списке."""

    def __init__(self, name: str) -> None:
        """Создать именованный пустой плейлист."""
        super().__init__()
        self.name = name
        self._current_node: Optional[LinkedListItem] = None

    @property
    def current(self) -> Optional[Composition]:
        """Вернуть текущую композицию."""
        return self._current_node.data if self._current_node is not None else None

    def play_all(self, item: Composition) -> None:
        """Начать последовательное проигрывание с указанной композиции."""
        self._current_node = self._find_node(item)

    def next_track(self) -> Optional[Composition]:
        """Перейти к следующей композиции с циклическим переходом."""
        if self._current_node is None and self._head is not None:
            self._current_node = self._head
        elif self._current_node is not None:
            self._current_node = self._current_node.next_item
        return self.current

    def previous_track(self) -> Optional[Composition]:
        """Перейти к предыдущей композиции с циклическим переходом."""
        if self._current_node is None and self._head is not None:
            self._current_node = self._head
        elif self._current_node is not None:
            self._current_node = self._current_node.previous_item
        return self.current

    def remove(self, item: object) -> None:
        """Удалить композицию и корректно обновить текущую позицию."""
        node = self._find_node(item)
        next_node = node.next_item
        was_current = node is self._current_node
        super().remove(node)
        if self._length == 0:
            self._current_node = None
        elif was_current:
            self._current_node = next_node if next_node is not None else self._head

    def move_composition(self, index_from: int, index_to: int) -> None:
        """Переместить композицию с одной позиции на другую."""
        if index_from < 0:
            index_from += len(self)
        if index_to < 0:
            index_to += len(self)
        if not 0 <= index_from < len(self) or not 0 <= index_to < len(self):
            raise IndexError("Индекс вне диапазона списка.")
        if index_from == index_to:
            return
        composition = self[index_from]
        self.remove(composition)
        if index_to == 0:
            self.append_left(composition)
        elif index_to >= len(self):
            self.append_right(composition)
        else:
            self.insert(self[index_to - 1], composition)
