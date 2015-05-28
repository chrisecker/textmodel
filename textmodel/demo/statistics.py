import gc
import sys
sys.path.insert(0, '..')

from textmodel import TextModel
from textmodel.treebase import depth, count



# Create a long text
text = TextModel()
for i in range(10000):
    text.append(TextModel("Line %i\n" % i))

# Colorize it!
colors = 'white', 'red'
i1 = 0
i2 = 10
while i2<len(text):
    text.set_properties(i1, i2, bgcolor=colors[i1%2])
    i1 = i2
    i2 += 10

# Remove garbage so that the statistics are correct
gc.collect() 
    
# Print some statistics
print "Length of text:", len(text)
print "Number of lines:", text.nlines()
print "Depth of texel tree:", depth(text.texel)
print "Number of texels in tree:", count(text.texel)
print "Number of objects in memory:", len(gc.get_objects())
