# Bug Report

## UUID
bf8a3685-45a0-46fd-885f-676591016639

## Код
```
#include <iostream>
#include <vector>
using namespace std;

int partition(vector<int>& arr, int low, int high) {
  
    // choose the pivot
    int pivot = arr[high];
  
    // undex of smaller element and indicates 
    // the right position of pivot found so far
    int i = low - 1;

    // Traverse arr[low..high] and move all smaller
    // elements on left side. Elements from low to 
    // i are smaller after every iteration
    for (int j = low; j <= high - 1; j++) {
        if (arr[j] < pivot) {
            i++;
            swap(arr[i], arr[j]);
        }
    }
    
    // move pivot after smaller elements and
    // return its position
    swap(arr[i + 1], arr[high]);  
    return i + 1;
}

// the QuickSort function implementation
void quickSort(vector<int>& arr, int low, int high) {
  
    if (low < high) {
      
        // pi is the partition return index of pivot
        int pi = partition(arr, low, high);

        // recursion calls for smaller elements
        // and greater or equals elements
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}

int main() {
    vector<int> arr = {10, 7, 8, 9, 1, 5};
    int n = arr.size();
    quickSort(arr, 0, n - 1);
  
    for (int i = 0; i < n; i++) {
        cout << arr[i] << " ";
    }
    return 0;
}
```

## Ответ нейросети (JSON)
```json
[{"t":"S","v":"partition(vector<int>& arr, int low, int high)"},{"t":"X","v":"pivot = arr[high]"},{"t":"X","v":"i = low - 1"},{"t":"F","v":"int j = low; j <= high - 1; j++","c":[{"t":"IF","v":"arr[j] < pivot","y":[{"t":"X","v":"i++"},{"t":"P","v":"swap(arr[i], arr[j])"}],"n":[]}]},{"t":"P","v":"swap(arr[i + 1], arr[high])"},{"t":"E","v":"return i + 1"},{"t":"S","v":"quickSort(vector<int>& arr, int low, int high)"},{"t":"IF","v":"low < high","y":[{"t":"X","v":"pi = partition(arr, low, high)"},{"t":"P","v":"quickSort(arr, low, pi - 1)"},{"t":"P","v":"quickSort(arr, pi + 1, high)"}],"n":[]},{"t":"E","v":"конец quickSort"},{"t":"S","v":"Начало"},{"t":"P","v":"quickSort(arr, 0, n - 1)"},{"t":"F","v":"int i = 0; i < n; i++","c":[{"t":"IO","v":"cout << arr[i] << \" \""}]},{"t":"E","v":"return 0"}]
```

## Списано токенов
4

## Комментарий
ПИЗДА ЭТА БЛОК СХЕМА РАЗРУШИЛА МНЕ ЖИЗНЬ БЛЯТЬБ

## Дата
2026-03-14 16:59:03
