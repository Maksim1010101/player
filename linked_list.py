"""Кольцевой двусвязный список для музыкального плейера."""

from collections.abc import Iterator
from typing import Any, Optional


class LinkedListItem:
    """Элемент списка, содержащий данные и ссылки на соседние элементы."""

    def __init__(self, data: Any) -> None:
        """Создать элемент с указанными данными."""
        self._data = data
        self._next: Optional["LinkedListItem"] = None
        self._previous: Optional["LinkedListItem"] = None

    @property
    def data(self) -> Any:
        """Вернуть данные элемента."""
        return self._data

    def __eq__(self, other: object) -> bool:
        """Сравнить узел с другим узлом или его данными."""
        if isinstance(other, LinkedListItem):
            return self._data == other._data
        return self._data == other

    @property
    def track(self) -> Any:
        """Вернуть композицию, хранящуюся в элементе."""
        return self._data

    @property
    def next_item(self) -> Optional["LinkedListItem"]:
        """Вернуть следующий элемент."""
        return self._next

    @next_item.setter
    def next_item(self, item: Optional["LinkedListItem"]) -> None:
        """Установить следующий элемент."""
        self._next = item
        if item is not None and item.previous_item is not self:
            item.previous_item = self

    @property
    def previous_item(self) -> Optional["LinkedListItem"]:
        """Вернуть предыдущий элемент."""
        return self._previous

    @previous_item.setter
    def previous_item(self, item: Optional["LinkedListItem"]) -> None:
        """Установить предыдущий элемент."""
        self._previous = item
        if item is not None and item.next_item is not self:
            item.next_item = self


class LinkedList(Iterator[Any]):
    """Кольцевой двусвязный список с обычным конечным обходом."""

    def __init__(self, first_item: Optional[LinkedListItem] = None) -> None:
        """Создать список, возможно начиная с уже созданного узла."""
        self._head = first_item
        self._length = self._count_nodes()
        self._current_iter: Optional[LinkedListItem] = None
        self._iterated = 0

    def _count_nodes(self) -> int:
        """Посчитать узлы в кольце и восстановить обратные ссылки."""
        if self._head is None:
            return 0
        count = 1
        node = self._head
        previous = node
        while node.next_item is not None and node.next_item is not self._head:
            node = node.next_item
            node.previous_item = previous
            previous = node
            count += 1
        previous.next_item = self._head
        self._head.previous_item = previous
        return count

    @property
    def first_item(self) -> Optional[LinkedListItem]:
        """Вернуть первый узел списка."""
        return self._head

    def _find_node(self, item: Any) -> LinkedListItem:
        """Найти узел по данным или вернуть ошибку."""
        if self._head is not None:
            node = self._head
            for _ in range(self._length):
                if node is item or node.data == item:
                    return node
                node = node.next_item  # type: ignore[assignment]
        raise ValueError("Элемент не найден в списке.")

    def append_left(self, item: Any) -> None:
        """Добавить данные в начало списка."""
        new_node = LinkedListItem(item)
        if self._head is None:
            new_node.next_item = new_node
            new_node.previous_item = new_node
            self._head = new_node
        else:
            tail = self._head.previous_item
            new_node.next_item = self._head
            new_node.previous_item = tail
            self._head.previous_item = new_node
            if tail is not None:
                tail.next_item = new_node
            self._head = new_node
        self._length += 1

    def append_right(self, item: Any) -> None:
        """Добавить данные в конец списка."""
        if self._head is None:
            self.append_left(item)
            return
        tail = self._head.previous_item
        new_node = LinkedListItem(item)
        new_node.next_item = self._head
        new_node.previous_item = tail
        self._head.previous_item = new_node
        if tail is not None:
            tail.next_item = new_node
        self._length += 1

    def append(self, item: Any) -> None:
        """Добавить данные в конец списка."""
        self.append_right(item)

    def remove(self, item: Any) -> None:
        """Удалить первый узел с указанными данными."""
        node = self._find_node(item)
        if self._length == 1:
            self._head = None
        else:
            previous = node.previous_item
            next_node = node.next_item
            if previous is not None:
                previous.next_item = next_node
            if next_node is not None:
                next_node.previous_item = previous
            if node is self._head:
                self._head = next_node
        node.next_item = None
        node.previous_item = None
        self._length -= 1

    def insert(self, previous: Any, item: Any) -> None:
        """Вставить данные после узла с данными ``previous``."""
        previous_node = self._find_node(previous)
        next_node = previous_node.next_item
        new_node = LinkedListItem(item)
        new_node.previous_item = previous_node
        new_node.next_item = next_node
        previous_node.next_item = new_node
        if next_node is not None:
            next_node.previous_item = new_node
        self._length += 1

    @property
    def last(self) -> Optional[LinkedListItem]:
        """Вернуть последний узел или ``None`` для пустого списка."""
        return self._head.previous_item if self._head is not None else None

    def __len__(self) -> int:
        """Вернуть число элементов."""
        return self._length

    def __iter__(self) -> "LinkedList":
        """Подготовить конечный обход списка от начала к концу."""
        self._current_iter = self._head
        self._iterated = 0
        return self

    def __next__(self) -> Any:
        """Вернуть следующий элемент конечного обхода."""
        if self._current_iter is None or self._iterated >= self._length:
            raise StopIteration
        data = self._current_iter
        self._current_iter = self._current_iter.next_item
        self._iterated += 1
        return data

    def __getitem__(self, index: int) -> Any:
        """Вернуть данные элемента по неотрицательному индексу."""
        if not isinstance(index, int):
            raise TypeError("Индекс должен быть целым числом.")
        if index < 0:
            index += self._length
        if index < 0 or index >= self._length or self._head is None:
            raise IndexError("Индекс вне диапазона списка.")
        node = self._head
        for _ in range(index):
            node = node.next_item  # type: ignore[assignment]
        return node.data

    def __contains__(self, item: Any) -> bool:
        """Проверить наличие данных в списке."""
        try:
            self._find_node(item)
        except ValueError:
            return False
        return True

    def __reversed__(self) -> Iterator[Any]:
        """Вернуть конечный обратный итератор."""
        if self._head is None:
            return iter(())
        node = self._head.previous_item
        values = []
        for _ in range(self._length):
            values.append(node.data)
            node = node.previous_item  # type: ignore[assignment]
        return iter(values)
