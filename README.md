# Simple-bulk-renamer
This python code uses the Windows command prompt to automatically rename files in bulk

I rebuilt this very simple program into something that has many more uses. 
**USAGE:**
1. You load a folder with multiple files you want to rename.
2. In the input field replace a part of the base naming convention with a variable enclosed in curly brackets
3. In the output field write how you'd like all the files to be named after. In the places where you want a variable, write it the same way as described before.
4. Below, you can see how the files will be named after.
5. Optionally, you can change how certain variables behave after conversion. There are two types:
  1) Integer - for numbers (frame numbers, etc.) - you can choose to add a set amount of digits (For example if you choose 4 then it would change 12 to 0012)
  2) String - for everything else - you can choose to change the capitalization or the seperating character
