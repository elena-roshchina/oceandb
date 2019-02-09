from django.test import TestCase

# Create your tests here.

somelist = [[1,2],[1,4],[10,2]]
somelist.sort(key=lambda i: i[1])
print(somelist)
