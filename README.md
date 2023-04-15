# Simple-bulk-renamer
This python code uses the Windows command prompt to automatically rename files in bulk

**Installation:**

Before using this program make sure you have the TQDM library installed.

To install the library, please run:
```
pip install tqdm
```

*If you do not have pip installed, please follow this tutorial:
https://www.dataquest.io/blog/install-pip-windows/*

**Usage:**

To use this program, you have to input a couple variables:

*The directory of the files* - when you see a windows file choice window pop up, please select the folder containing all of the files you wish to rename

*The number of the files* - the integer number for the files you want to rename (the program counts from 1, not zero)

*The previous number of digits* - the total number of digits there are in each number in the current numbering system of the files.
For example:
01 - two digits
001 - three digits
If your numbering system does not add any zeros (1, 10, 100) please input zero

*The target number of digits* - again, the number of digits (the zero thing still works) that you wish for the files to have after renaming

*The previous naming form* - The format in which the files are currently named with a # included where the number is.
For example:
Frame_#.png would be:
Frame_001.png 

*The target naming form* - Again, the format of naming with the hashtag, except how you want them to be named

**If you have any questions, be sure to put them into the issues tab**
