# HKMU-2090SEF-Course-Project
Task1&amp;Task2

HKMU COMP2090SEF GRP_105

This Project is mainly use for the 2090SEF course project (Preliminary code submission).

Contributors:
14239505 CHAN Tsz Shun
14251198 Ding Xingxi
14276090 YU Haoxiang


<h1>Task 1</h1>  


<h2>User Guide (how to run Python code)</h2>

1. Download the original .py file called "calendarv5" on the main page
2. Use IDEs (e.g. Visual Studio Code, Pytharm) to open it
3. Select debugging mode
4. Directly running the program in IDEs

Introduction video link : 
https://youtu.be/-rIxVfAVtuc <b>(Recommended)</b>
https://www.youtube.com/watch?v=UgC0Jx-LBA4 (Incompleted)


We are currently working on designing a portable student calendar program using OOP framework, which allows users to select dates and add to-do lists. 

<img width="1028" height="622" alt="image" src="https://github.com/user-attachments/assets/431c65f9-df81-47c8-b8fd-37d0b5f5f347" />

*GUI Interface*
Only used for verifying the save function: This module aims to deal with the problem that program delete all stored todo list parameters automatically after user closed the program.

<h2>Features</h2>

1."CalendarTodoApp" : Lightweight initialization calendar module
   ``` python
    class CalendarTodoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("920x560")
        self.minsize(860, 500)

        self.store = TodoStore(DATA_FILE)

        today = date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_day = today

        self._build_ui()
        self._render_calendar()
        self._refresh_todo_list()
```
We used the most concise architecture possible to write the GUI. Self-calling fuctions have been used inside it.

2.Encapsulation & Composition in calendar data storing
``` python
class TodoStore:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data: dict[str, list[TodoItem]] = {}
        self.ensure_data_dir()
        self.load()

    def ensure_data_dir(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.file_path.exists():
            self.data = {}
            self.save()
            return
```

In order to prevent data from being easily lost when closing the program, we created "TodoStore" module and established a long-term storage module using instantiated objects and other methods.


<h2>What's Next</h2>  

<b>Advanced supporting methods</b> is still in planning status.
In future development we have planned to design a feature that can repeat <b>multiple cycles</b>, rather than displaying it all at once.


<h1>Task 2</h1>

<h2>A) Binary Tree Data Structure</h2>

A non-linear and hierarchincal conceptual model where every node has at most two children. Also, each node is build-up by three components: Data, left and right child pointers.

<h2>User Guide (how to run Python code)</h2>

<h2>B) Shell Sort Algorithm</h2>

An in-place comparison sort which allows elements exchange in datasets by comparing through larger distances in initial stages, and reduce gap size and required swaps times to catalytic the process. 

<h2>User Guide (how to run Python code)</h2>

Question: How to sort out the list [61, 9, 62, 83, 37, 80, 32, 45, 93] by using Shell sort algorithm?

Step 1: Choose a suitable gap sequence in initial stages, like (n/2 or n/4) in common. 

        -> Divide the list into several subarrays.
        
        -> Time complexity depends on gap sequence chosen uniquely.

Step 2: Elments would sort in each subarrays by using insertion sort.

Step 3: The gap subside until becomes 1 after operate the process repeatedly like the code below. 

``` python
def shell_sort(arr):
    size = len(arr)
    gap = size // 2

    while gap > 0:
        for i in range(gap, size):
            anchor = arr[i]
            j = i
            while j >= gap and arr[j-gap] > anchor:
                arr[j] = arr[j-gap]
                j -= gap
            arr[j] = anchor
        gap = gap // 2

if __name__ == '__main__':
    elements = [61, 9, 62, 83, 37, 80, 32, 45, 93]
    shell_sort(elements)
    print(elements)
```

Hence, it would sort out the list [61, 9, 62, 83, 37, 80, 32, 45, 93] by using Shell sort algorithm and results as:

``` python
[9, 32, 37, 45, 61, 62, 80, 83, 93]
```
