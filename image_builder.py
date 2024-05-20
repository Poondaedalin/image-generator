from PIL import Image, ImageDraw
import random
import math

### Global Variables Start Here! ###
# Edit them at your leisure!

G_DESTAGNATE = False
G_DESTAGNATE_RATE = 25
# When True, enables a destagnation protocol. 
# After multiple trials with no improvement, gradually ramps up mutation count over time until an improvement occurs.
# It's unclear if this actually affects the rate of change or the chance of getting entirely stuck, but it FEELS impactful, and sometimes that's all that matters :p

G_VERBOSITY = 2
# Verbosity <= 0: Disable all printing 
# Verbosity = 1: Display improvements
# Verbosity >= 2: Display each generation

G_USE_HSV = False
# When True, uses (Hue Saturation Value) instead of (Red Green Blue) channels. Slows down significantly when True.

G_GENERATE_GIF = False
# If True, generates a GIF of each image that marked an improvement in fitness. The GIF is created once the trial has ended (Ctrl-C will not work!)
# Warning: this could be a VERY long GIF depending on the input image and parameters.

G_MAX_DESTAG = 750
# Terminates the current trial and renders the final image after the current trial goes this many generations with no progress.
# I'd recommend setting this number to be high, but not too high (somewhere between 200 - 1500).

G_REFLUX_POP = False
# When True, wipes the current population at the start of each trial, and replaces them with random new Species.
# When False, the population is maintained throughout each trial.

G_CULLING = 2
# Controls how many of the worst-performing Species are killed off and replaced by new offspring.
# Recommended to be kept as an even number less than or equal to half of G_POP_SIZE.

G_NUM_RECTS = 256
# This can be any amount that you want. Bear in mind that more rects means slower work, but it also means a more precise end-product.

G_NUM_MUTATIONS = math.floor(G_NUM_RECTS**(1/2))
# This can be any integer, but I'd recommend keeping it somewhere between 1-16. (it generally caps around 64)

G_NUM_GLOBAL_MUTATIONS = 2
# Defaults to 0. Applies mutations to all members of the population EXCEPT the best two.

G_POP_SIZE = 4
# Again, this can be any integer, but you'll quickly see the performance impact for larger populations. Recommended at somewhere between 4 - 16.

G_WIDTH, G_HEIGHT = (32,32)
# Both dimensions should be the same power of 2!

G_ENABLE_OPS = False
# When enabled, allows the algorithm to make minute adjustments to the values. Potentially unstable, and may impact performance for larger populations/codes.

G_ENABLE_ALPHA = False
# When enabled, allows Alpha to be changed as well. Recommended to be False for images with sharp outlines, and recommended to be True for images with soft edges.

G_LOG_LEN = math.floor(math.log2(G_WIDTH))
# Used internally as the code length for x-pos, y-pos, width, and height. Do not touch!

G_RECT_CODE = G_LOG_LEN*4 + 32
# Used internally as the total code length. Don't touch this either!

G_FITNESS_POWER = 2

G_FITNESS_WEIGHT_A = 1
G_FITNESS_WEIGHT_B = 1
G_FITNESS_WEIGHT_C = 1
# Can either be used to apply extra weight to the RGB or HSV channels when defining fitness.

G_SHUFFLE_LAYERS = False
# When enabled, draws the rectangles to the canvas in a random order. Not fully tested!

G_START_INDEX = 0
G_END_INDEX = 60
image_list = [Image.open('isaac\\isaac' + str(x) + '.png') for x in range(1,G_END_INDEX+1)]

# If you want to use a specific image, use its filename as the source image instead and ignore the iterator!

#image_list = [Image.open('title_screen_small.jpg')]
# Fairly certain it works with JPG, WEBP, AVIF, etc., but I haven't tested it. When in doubt, use a PNG!


### Classes and Functions Start Here! ###
# Don't edit these unless you know what you're doing!

def decode(arr):
    # Given an array of True and False booleans, returns the integer representation of its binary string.
    # Example: [True, False, True, True, False, True] = 101101 = 45
    out_str = ""
    for a in arr:
        out_str = out_str + (a and "1" or "0")
    return out_str != "" and int(out_str,2) or 0

def op(arr, op, factor):
    out_arr = []
    format_base = (G_WIDTH == 256 and '{0:08b}') or (G_WIDTH == 128 and '{0:07b}') or (G_WIDTH == 64 and '{0:06b}') or (G_WIDTH == 32 and '{0:05b}') or (G_WIDTH == 16 and '{0:04b}') or (G_WIDTH == 8 and '{0:03b}') or (G_WIDTH == 4 and '{0:02b}') or (G_WIDTH == 2 and '{0:01b}') or (G_WIDTH == 1 and '{0:00b}')
    if op == "+":
        str_in = format_base.format((decode(arr) + factor) % 256)
    elif op == "-":
        str_in = format_base.format((decode(arr) - factor) % 256)
    else:
        return [False for i in range(G_LOG_LEN)]
    for i in range(len(str_in)):
        out_arr.append(str_in[i] == '1')
    return out_arr

class Species:
    def __init__(self,rect_num):

        self.genetic_code = [random.choice([True,False]) for i in range(G_RECT_CODE*rect_num)]
        #self.genetic_code = [True for i in range(64*rect_num)]

        # defines x rectangles
        # for a canvas of size 256x256:
            # 8 bits for x-value
            # 8 bits for y-value
            # 8 bits for x-size
            # 8 bits for y-size
            # 8 bits for R
            # 8 bits for G
            # 8 bits for B
            # 8 bits for A
            # 64 bits total for each rectangle

        pass

    def mutate(self):
            
             # For each mutation:
                #   - Flip a random bit in the genetic code from False to True or vice versa
                #   - If G_ENABLE_OPS is True, 50% chance to instead either add 1 or subtract 1 from a random variable.

            for _ in range(G_NUM_MUTATIONS):
                rng = random.randint(0,1)
                if rng == 1 and G_ENABLE_OPS:
                    r_index = random.randint(1,7)
                    sel_op = (random.randint(0,1) == 0) and "+" or "-"
                    self.genetic_code = self.genetic_code[:((r_index*8))] + op(self.genetic_code[(r_index*8):(((r_index+1)*8))], sel_op, random.randint(1,20)) + self.genetic_code[((r_index+1)*8):]
                    pass
                else:
                    r_index =  random.randint(0,len(self.genetic_code)-1)
                    self.genetic_code[r_index] = not self.genetic_code[r_index]

    def mate(self,other):

        # Takes two Species and has them ""mate""
        # Picks a random point between the first and third quartile of the code and splits both codes along that point.
        # Child A gets the first part of Parent A's code and the second part of Parent B's code.
        # Child B gets the first part of Parent B's code and the second part of Parent A's code.

        new_self = Species(G_NUM_RECTS)
        new_other = Species(G_NUM_RECTS)
        split_point = random.randint(math.floor(0.25*len(self.genetic_code)),math.floor(0.75*len(self.genetic_code)))
        new_self.genetic_code = self.genetic_code[:split_point] + other.genetic_code[split_point:]
        new_other.genetic_code = other.genetic_code[:split_point] + self.genetic_code[split_point:]
        return (new_self, new_other)

    def get_image(self):

        # Generates an image based on the genetic code.
        # Each code transcribes a number of rectangles with an (x,y), width, height, and color.
        # Alpha is unused (but rather acts as a buffer space where mutations can freely occur with no effect on the output).

        img = Image.new(G_USE_HSV and "HSV" or "RGBA", (G_WIDTH-1, G_HEIGHT-1), color = G_USE_HSV and (0,0,255,255) or (255,255,255,255))
        draw = ImageDraw.Draw(img)

        members = []

        for i in range(0,len(self.genetic_code),G_RECT_CODE):
            x = decode(self.genetic_code[i:i+G_LOG_LEN-1])
            y = decode(self.genetic_code[i+G_LOG_LEN:i+(G_LOG_LEN*2-1)])
            width = decode(self.genetic_code[i+(G_LOG_LEN*2):i+(G_LOG_LEN*3-1)])
            height = decode(self.genetic_code[i+(G_LOG_LEN*3):i+(G_LOG_LEN*4-1)])
            r = decode(self.genetic_code[i+(G_LOG_LEN*4):i+(G_LOG_LEN*4+8)])
            g = decode(self.genetic_code[i+(G_LOG_LEN*4+8):i+(G_LOG_LEN*4+16)])
            b = decode(self.genetic_code[i+(G_LOG_LEN*4+16):i+(G_LOG_LEN*4+24)])
            #a = 255
            a = G_ENABLE_ALPHA and decode(self.genetic_code[i+(G_LOG_LEN*4+24):i+(G_LOG_LEN*4+32)]) or 255
            members.append((x,y,width,height,r,g,b,a))

        if G_SHUFFLE_LAYERS: random.shuffle(members)

        for mem in members:
           (x,y,width,height,r,g,b,a) = mem
           draw.rectangle([(x,y),(x+width,y+height)], fill=(r,g,b,a))
        
        return img

    def fitness(self,gen_output,num):

        # The fitness is calculated by taking the distance between the current genetic code's image and the target image, pixel by pixel.

        canvas1 = self.get_image()
        
        canvas2 = Image.new(G_USE_HSV and "HSV" or "RGBA", (G_WIDTH-1, G_HEIGHT-1), "black")
        canvas2.paste(source_img,(0,0))

        p1 = list(canvas1.getdata())
        p2 = list(canvas2.getdata())

        sum_fitness = 0

        for c in range(0,len(p1)):

            curr_p1 = p1[c]
            curr_p2 = p2[c]
            
            sum_fitness = sum_fitness + ((((curr_p2[0] - curr_p1[0])*G_FITNESS_WEIGHT_A)**G_FITNESS_POWER + ((curr_p2[1] - curr_p1[1])*G_FITNESS_WEIGHT_B)**G_FITNESS_POWER + ((curr_p2[2] - curr_p1[2])*G_FITNESS_WEIGHT_C)**G_FITNESS_POWER))

        try: 
            if gen_output:
                canvas1 = canvas1.convert("RGB")
                canvas1.save("test" + str(num+1) + ".png", "PNG")
        except OSError:
            pass

        return sum_fitness
    

### Driver Code Starts Here! ###
# Don't edit this either (unless you know what you're doing, in which case, go nuts!)

population = [Species(G_NUM_RECTS) for i in range(G_POP_SIZE)]
# Although the Species has their code randomized by default, they can be initialized to have pre-defined code if needed.
# Example code:

#   darwin = Species(G_NUM_RECTS)
#   darwin.genetic_code = [False for i in range(G_RECT_CODE*G_NUM_RECTS)]
#   population.append(darwin)
#   The code inside the brackets can be replaced with your own values, but bear in mind that the number of entries must match G_RECT_CODE*G_NUM_RECTS. 

for i in range(G_START_INDEX, len(image_list)):

    if G_REFLUX_POP: population = [Species(G_NUM_RECTS) for _ in range(G_POP_SIZE)]

    img = image_list[i] 
    source_img = img
    g = 0

    past_best_fit = 0
    num_stagnate = 0
    render_list = []

    while G_MAX_DESTAG <= 0 or num_stagnate < G_MAX_DESTAG:
        
        if G_DESTAGNATE:
            G_NUM_MUTATIONS = min(num_stagnate//G_DESTAGNATE_RATE + 1,G_RECT_CODE)

        population = sorted(population, key = lambda x: x.fitness(False,i))

        options = list(range(0,len(population)-2))
        random.shuffle(options)

        for _ in range(G_CULLING//2):

            population.pop()
            population.pop()

            (new1, new2) = population[options[0]].mate(population[options[1]])

            new1.mutate()
            new2.mutate()

            population.append(new1)
            population.append(new2)

        best_fit = population[0].fitness(True,i)

        if G_DESTAGNATE and G_VERBOSITY > 1:
            print("Generation " + str(g) + ": " + str(best_fit) + " : " + str(i) + " : " + str(num_stagnate//G_DESTAGNATE_RATE + 1))

        elif G_VERBOSITY > 1:
            print("Generation " + str(g) + ": " + str(best_fit) + " : " + str(i) + " : " + str(num_stagnate))
            pass

        if past_best_fit <= best_fit:
            num_stagnate = num_stagnate + 1
        else:
            num_stagnate = 0
            if G_GENERATE_GIF:
                render_list.append(population[0].get_image())
            if G_VERBOSITY == 1:
                print("Improvement : " + str(best_fit - past_best_fit))
                #print("".join([(x and "1" or "0") for x in population[0].genetic_code]))

        past_best_fit = best_fit

        g = g + 1

    if G_GENERATE_GIF:
        render_list[0].save("time_morph.gif", save_all=True, format="GIF", append_images=render_list, optimize=False, duration=2000//len(render_list), loop=1)