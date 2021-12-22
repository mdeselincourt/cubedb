import sqlite3
import itertools
connection = sqlite3.connect('cubedb.sqlite')
cursor = connection.cursor()

colours = ["W","U","B","R","G"]
colourPairs = list(itertools.combinations(colours, r=2))
synergies = []

for c1, c2 in colourPairs:
	# print(c1, c2)

	query = '''SELECT
		'{c1}{c2}',
		Synergies.Synergy,
		COUNT(CASE WHEN Synergies.RolePlayed='Payoff' THEN 1 END) as Payoffs, 
		COUNT(CASE WHEN Synergies.RolePlayed='Participant' THEN 1 END) as Participants,
		(COUNT(CASE WHEN Synergies.RolePlayed='Payoff' THEN 1 END) * COUNT(CASE WHEN Synergies.RolePlayed='Participant' THEN 1 END))  as Product 
	FROM Synergies
	INNER JOIN Cards ON Cards.Card=Synergies.Card
	WHERE (Cards.{c1} = 1 OR Cards.{c2} = 1)
	GROUP BY Synergies.Synergy
	ORDER BY (COUNT(CASE WHEN Synergies.RolePlayed='Payoff' THEN 1 END) * COUNT(CASE WHEN Synergies.RolePlayed='Participant' THEN 1 END)) DESC;'''.format(c1=c1,c2=c2)

	for synergyTuple in cursor.execute(query):
		synergies.append(synergyTuple)

def synergyScore(synergyTuple):
	return synergyTuple[4]

# Sort (for ease of log-browsing)
synergies.sort(key=synergyScore,reverse=True)

for s in synergies:
	print(s)
	
unfoundPairs = colourPairs

while len(unfoundPairs) > 0:
	match = next((s for s in synergies if tuple(s[0]) in unfoundPairs), None)
	print(match)
	unfoundPairs.remove(tuple(match[0]))
	

	
