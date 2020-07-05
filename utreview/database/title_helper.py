
def to_title(sen):

	__articles = ['a', 'an', 'the']
	__
	words = sen.split()

	for i in range(len(words)):
		
		if i == 0 or i == words.length-1:
			words[i] = words[i].title()
