import os
from tqdm import tqdm

# Ask for folder directory
print("Input the folder directory")
from tkinter.filedialog import askdirectory

path = askdirectory(title='Select Folder') # shows dialog box and return the path
print(path)

while True: # Asks for number of files to rename
    try:
        number = int(input("Please input the number of files to rename: "))
        break
    except ValueError:
        print("Please input a valid integer")

print("The number you entered is ", number)

while True: # Asks for the start number of the file names
    try:
        start_number = int(input("Please input the number of the first file (input 0 when the naming starts from 1): "))
        if start_number == 0:
            print('The program will look for files starting from 1')
        else:
            print("The program will look for files starting from ", start_number)
            start_number = start_number - 1

        break
    except ValueError:
        print("Please input a valid integer")

while True: # Asks for number of digits of the numbering system
    try:
        digits = int(input("Please input the number of digits of the previous naming system (input 0 when there are no zeros added): "))
        if digits == 0:
            print('The program will not look for any additional zeros')
        else:
            print("The current number of digits you entered is ", digits)
        break
    except ValueError:
        print("Please input a valid integer")

while True: # Asks for number of digits of the target numbering system
    try:
        target_digits = int(input("Please input the number of digits in the target naming system (input 0 when there are no zeros added): "))
        if target_digits == 0:
            print('The program will not add any additional zeros')
        else:
            print("The target number of digits you entered is ", target_digits)

        break
    except ValueError:
        print("Please input a valid integer")

while True: # Input the previous naming form
    previous_form = input('Please input the form of the name of files to rename (include "#" where there is the number of the file and make sure the file extension is included): ')
    if previous_form.count("#") == 1:
        break
    elif previous_form.count("#") == 0:
        print("The string does not contain a hashtag. Please try again.")
    else:
        print("The string contains more than one hashtag. Please try again.")
        
while True: # Input the target naming form
    target_form = input('Please input the target form of the name of files to be renamed to (include "#" where there is the number of the file and make sure the file extension is included): ')
    if target_form.count("#") == 1:
        break
    elif target_form.count("#") == 0:
        print("The string does not contain a hashtag. Please try again.")
    else:
        print("The string contains more than one hashtag. Please try again.")
        
print('All variables inputted correctly. Please stand by while the program renames the files.')

def insertnum(form, number, d): # Define the function for inserting numbers into the forms
    if d == 0:
        return form.replace("#", str(number))
    else:
        halves = form.split("#")
        padded_number = "{:0>{}}".format(number, d)
        return(str(halves[0]) + str(padded_number) + str(halves[1]))

if start_number == 0:
    for i in tqdm(range(number), desc='Progress:', unit='file', ascii=True): #Run the renaming loop with exceptions for parenthisis
        os.chdir(path)
        prev_name = insertnum(previous_form, int(i + 1), digits)
        target_name = insertnum(target_form, int(i + 1), target_digits)
        prev_name_escaped = prev_name.replace('"', '\\"')
        target_name_escaped = target_name.replace('"', '\\"')
        os.rename(str(prev_name_escaped), str(target_name_escaped))
else:
    number = number + start_number
    var = 1
    for i in tqdm(range(start_number, number), desc='Progress:', unit='file', ascii=True): #Run the renaming loop with exceptions for parenthisis
        os.chdir(path)
        prev_name = insertnum(previous_form, int(i + 1), digits)
        target_name = insertnum(target_form, int(var), target_digits)
        prev_name_escaped = prev_name.replace('"', '\\"')
        target_name_escaped = target_name.replace('"', '\\"')
        os.rename(str(prev_name_escaped), str(target_name_escaped))
        var += 1
    
print('The files have been succesfully converted, thank you for your patience!')
