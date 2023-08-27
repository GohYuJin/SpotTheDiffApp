import os
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import logging
import numpy as np

im_root = "resources/images"
ans_root = "resources/answers"

class Main(object):

    def __init__(self):
        self.canvas = None
        self.clicks = []
        self.image_used = None
        self.canvas_size = (1200, 750)

        self.ori_white_border = 36 # the image has a white border of 36 pixels
        self.ori_click_width = 15
        self.downsample_ratio = 1.0
        self.answers = []
        self.correct = np.array([0])
        self.total_score = 0
        self.total_differences = 0
        self.resources = {"images":[], "answers":[]}
        for i in os.listdir(im_root):
            ans_path = os.path.join(ans_root, ".".join(os.path.split(i)[1].split(".")[0:-1]) + ".txt")
            if os.path.exists(ans_path):
                self.resources["images"].append(os.path.join(im_root, i))
                self.resources["answers"].append(ans_path)
        self.res_id = -1
        logging.basicConfig(filename="mouse_log.txt", level=logging.DEBUG, format="%(asctime)s: %(message)s")


    def downsample(self, ratio):
        self.white_border = int(self.ori_white_border * ratio)
        self.click_width = int(self.ori_click_width * ratio)
        self.answers = self.answers * ratio
        self.downsample_ratio = ratio


    def calc_inter_percent(self, clickBox, gtBox):
	      # determine the (x, y)-coordinates of the intersection rectangle
	      xA = max(clickBox[0], gtBox[0])
	      yA = max(clickBox[1], gtBox[1])
	      xB = min(clickBox[2], gtBox[2])
	      yB = min(clickBox[3], gtBox[3])
	      # compute the area of intersection rectangle
	      interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
	      # compute the area of the prediction box
	      clickBoxArea = (clickBox[2] - clickBox[0] + 1) * (clickBox[3] - clickBox[1] + 1)
	      # compute the percent intercented with ground-truth
	      inter_percent = interArea / float(clickBoxArea)
	      return inter_percent


    def verify_click(self, box):
        correct = False
        for idx, i in enumerate(self.answers):
            if self.calc_inter_percent(box, i) > 0.3:
                self.correct[idx] = 1
                correct = True
        return correct


    def update_score(self, correct):
        score = self.correct.sum()
        if correct:
            self.total_score += 1

        if score == len(self.correct):
            messagebox.showinfo("Congrats", "Congrats, You found all {0} differences".format(score))
            self.res_id += 1
            if self.res_id > len(self.resources["images"]) - 1:
                messagebox.showinfo("Game completed", "You have completed all images and found " 
                                     "{0}% ({1}/{2}) of all differences".format(
                                       round(self.total_score / self.total_differences * 100, 2),
                                       self.total_score, self.total_differences))
                self.root.destroy()
                quit()

            self.load_resources(self.resources["images"][self.res_id],
                                self.resources["answers"][self.res_id]
                                )
            self.canvas.itemconfig(self.image_container, image=self.image_used)
            while len(self.clicks) > 0:
                self.canvas.delete(self.clicks.pop())


    def on_left_button_press(self, event):
        logging.info("Mouse Clicked at ({0}, {1}) with {2}".format(event.x, event.y, "Button.left"))
        python_red = "#FF0000"
        python_green = "#00FF00"
        im_width = self.canvas_size[0]
        x1, y1 = (event.x - self.click_width), (event.y - self.click_width)
        x2, y2 = (event.x + self.click_width), (event.y + self.click_width)
        outline = python_red

        if event.x > im_width//2:
            x1, x2 = x1 - im_width//2 - self.white_border//2, x2 - im_width//2 - self.white_border//2

        correct = self.verify_click([x1, y1, x2, y2])
        if correct:
            outline = python_green

        click = self.canvas.create_oval(x1, y1, x2, y2, outline=outline, width=3)
        self.clicks.append(click)
        second_oval = self.canvas.create_oval(x1 + im_width//2 + self.white_border//2, y1,
                                      x2 + im_width//2 + self.white_border//2, y2, 
                                      outline=outline, width=3)
        self.clicks.append(second_oval)
        self.update_score(correct)
        
        print(int(x1/self.downsample_ratio), int(y1/self.downsample_ratio), 
        int(x2/self.downsample_ratio), int(y2/self.downsample_ratio))


    def on_left_button_release(self, event):
        x1, y1 = (event.x, event.y)
        logging.info("Mouse Released at ({0}, {1}) with {2}".format(
          event.x, event.y, "Button.left"))


#     def on_right_button_press(self, event):
#         logging.info("Mouse Clicked at ({0}, {1}) with {2}".format(
#         event.x, event.y, "Button.right"))
#         self.canvas.delete(self.clicks.pop()) #remove duplicate circle
#         self.canvas.delete(self.clicks.pop()) #remove original click


    def load_resources(self, im_path, gt_path):
        print("Loading image {0}".format(os.path.split(im_path)[1]))
        logging.info("Loading image {0}".format(os.path.split(im_path)[1]))

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight() - 100

        # Retrieve image
        image = Image.open(im_path)
        self.original_width, self.original_height = image.size[0:2] 

        width_ratio = screen_width/self.original_width
        height_ratio = screen_height/self.original_height

        if width_ratio >= 1 and height_ratio >= 1:
            self.canvas_size = (self.original_width, self.original_height)
        elif width_ratio > height_ratio:
            self.canvas_size = (int((self.original_width / self.original_height) * screen_height), screen_height)
        else:
            self.canvas_size = (screen_width, int((self.original_height / self.original_width) * screen_width))

        answers = []
        for i in open(gt_path, "r").read().split("\n"):
            answers.append([int(j) for j in i.split(" ")])
            self.total_differences += 1
        self.answers = np.array(answers)
        self.correct = np.zeros(len(self.answers), dtype=np.int0)
        self.downsample(self.canvas_size[0]/self.original_width)
        image = image.resize(self.canvas_size, Image.ANTIALIAS)
        self.image_used = ImageTk.PhotoImage(image)


    def main(self):
        self.root = Tk()
        self.root.title('Spot the difference')

        self.res_id = 0

        self.load_resources(self.resources["images"][self.res_id], 
                            self.resources["answers"][self.res_id])

        # Right side of the screen / image holder
        right_frame = Frame(self.root, 
                            width=self.canvas_size[0], 
                            height=self.canvas_size[1], 
                            cursor="dot")
        right_frame.pack(side=LEFT)

        self.canvas = Canvas(right_frame, width=self.canvas_size[0], height=self.canvas_size[1])
        self.image_container = self.canvas.create_image(0, 0, image=self.image_used, anchor="nw")

        # Create canvas
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_left_button_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_button_release)
        # self.canvas.bind("<Button-3>", self.on_right_button_press)
        # messagebox.showinfo("Time Countdown", "Time's up ")
        mainloop()




if __name__ == "__main__":
    Main().main()




