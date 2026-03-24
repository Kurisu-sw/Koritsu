# Bug Report

## UUID
55b98cd4-ee95-439c-8937-a53ee6e5f939

## Код
```
#include <stdio.h>

int main() {
    int i = 10;
    do {
        printf("Этот текст выведется один раз\n");
    } while (i < 5); // Условие ложно
    return 0;
}

```

## Ответ нейросети (JSON)
```json
START "Начало"
EXEC "i = 10"
PROCESS "Вывод: Этот текст выведется один раз"
WHILE "i < 5"
END
STOP "Конец"
```

## Списано токенов
34

## Комментарий


## Дата
2026-03-22 12:06:42
