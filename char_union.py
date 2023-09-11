import time
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os


# config
pix_per_char = 300
pix_for_timestamp = 20

font_support_dict = {
    "simhei": "simhei.ttf",
    "Deng": "Deng.ttf",
    "simsun": "simsun.ttc",
    "simkai": "simkai.ttf",
}

char_color= (255, 255, 255)      # white
bg_color = (0, 0, 0)           # black
split_color = (127, 127, 127)   # gray
ans_color_list = [
    np.array([[[127,127, 0]]]),    # yellow
    np.array([[[0, 0, 40]]]),    # blue
    np.array([[[160, 0, 0]]]),      # red
]

font_for_timestamp = ImageFont.truetype(font_support_dict["simhei"], pix_for_timestamp)  # Font type

os.makedirs("output", exist_ok=True)


def chars_to_bin_mat(chars: str, font: str, pix_for_timestamp: int):
    """ 
    The `chars_to_bin_mat` function takes a string `chars` and a string `font` as input parameters. It generates a binary matrix representation of the characters using the specified font.

    Parameters:
    - `chars` (str): The input string containing the characters to be converted to a binary matrix.
    - `font` (str): The font to be used for rendering the characters. If not provided, the default font is "simhei".

    Returns:
    - `bin_mat` (ndarray): The binary matrix representation of the characters, where each element represents a pixel in the image.

    Note:
    - The function uses the `ImageFont` module from the Python Imaging Library (PIL) to load the specified font.
    - The `pix_per_char` variable represents the desired pixel size for each character.
    - The function creates a new RGB image with a width equal to the number of characters multiplied by `pix_per_char` and a height of `pix_per_char`.
    - The characters are rendered onto the image using the specified font and color.
    - If a character is a whitespace, a white square is drawn at the corresponding position.
    - The resulting image is saved as "output/char.png".
    - The image is then converted to a binary matrix by dividing each pixel value by 255 and converting it to an unsigned 8-bit integer.
    - The binary matrix is returned as the output of the function.
    """

    # default font: simhei
    font = ImageFont.truetype(font_support_dict.get(
            font, 
            font_support_dict["simhei"]
        ), pix_per_char)  # Font type
        
    char_num = len(chars)
    width, height = char_num * pix_per_char, pix_per_char + pix_for_timestamp
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    for idx, char in enumerate(chars):
        position = (idx * pix_per_char, 0)
        if char.isspace():
            # draw a white square
            end = (idx * pix_per_char + pix_per_char, pix_per_char)
            draw.rectangle([position, end], fill=char_color)
        else:
            draw.text(position, char, font=font, fill=char_color)
        draw.text(position, char, font=font, fill=char_color)
    image.save("output/char.png")
    bin_mat = (np.array(image) / 255).astype(np.uint8)
    return bin_mat



def validate_chars_list(chars_list: List[str]) -> Optional[List[str]]:
    """
    This function validates a list of strings (chars_list). The function checks the following conditions:
    1. If any string in the list is empty or contains only whitespace, the function returns None.
    2. If more than one string in the list is of length 1, the function returns None.
    3. If more than one string in the list has a length different from 1, the function returns None.
    
    If all conditions are met, the function modifies the list as follows:
    - For strings of length 1, it repeats the string a number of times equal to the length of the first string in the list that is not of length 1.
    - For all other strings, it leaves them as they are.
    
    The function then returns the modified list.
    
    Parameters:
    chars_list (List[str]): The list of strings to validate and modify.
    
    Returns:
    Optional[List[str]]: The modified list of strings if all conditions are met, None otherwise.
    """
    # remove empty chars line
    chars_list = [chars for chars in chars_list if chars]
    
    # multi line one char and some line longer than one char
    one_len_chars = [chars for chars in chars_list if len(chars) == 1]
    if len(one_len_chars) > 1 and max([len(chars) for chars in chars_list]) > 1:
        return None
    
    # other lines not equal length
    lens_list = [len(chars)for chars in chars_list if len(chars) != 1]
    if len(set(lens_list)) > 1:
        return None
    
    lens = lens_list[0] if lens_list else 1
    new_chars_list = []
    for chars in chars_list:
        if len(chars) == 1:
            new_chars_list.append(chars * lens)
        else:
            new_chars_list.append(chars)
    return new_chars_list


def make_char_union_image(chars_list: List[str], font:str=None) -> Optional[Tuple[str]]:
    """
    This function takes a string of text as input, splits it into a list of characters, 
    validates the list, and then converts each character into a binary matrix. 
    It then multiplies all the binary matrices together to create a single image. 
    The image is then saved with a timestamp and the first character of each character 
    in the list as the filename.

    Parameters:
    text (str): The input string to be converted into an image.

    Returns:
    str: The path where the image is saved if the operation is successful, None otherwise.
    """
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    img_q_save_path = f'output/{timestamp}-{"|".join([chars for chars in chars_list])}_Q.png'
    img_a_save_path = f'output/{timestamp}-{"|".join([chars for chars in chars_list])}_A.png'

    valid_chars_list = validate_chars_list(chars_list)
    if valid_chars_list is None:
        return None
    
    # make binary mat as image for each valid line of input
    bin_mat_list = [chars_to_bin_mat(chars, font=font, pix_for_timestamp=pix_for_timestamp) for chars in valid_chars_list]
    
    # make question image
    prod = 255
    for bin_mat in bin_mat_list:
        prod = prod * bin_mat
    img_q = Image.fromarray(prod.astype(np.uint8))
    ImageDraw.Draw(img_q).text((0, pix_per_char), timestamp, font=font_for_timestamp, fill=split_color)
    img_q.save(img_q_save_path)

    # make answer image
    h, w, _ = bin_mat_list[0].shape
    summ = np.zeros((h, w, 3))
    for idx, bin_mat in enumerate(bin_mat_list):
        color = ans_color_list[idx]
        summ += bin_mat[:, :, idx:idx+1].reshape((h, w, 1)) @ color.reshape((1, 1, 3))
    coef = 255  # cannot devide by zero
    img_a = Image.fromarray((coef * summ).astype(np.uint8))
    ImageDraw.Draw(img_a).text((0, pix_per_char), timestamp, font=font_for_timestamp, fill=split_color)
    img_a.save(img_a_save_path)


    return (img_q_save_path, img_a_save_path)

if __name__=="__main__":
    # chars_list = ["榆木华","赤蛮奇", "",]
    chars_list = [" 划艇归","臧 家日", "地沟 旧",]
    print(make_char_union_image(chars_list, font='simhei'))
