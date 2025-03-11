#Creation of Hangman Greek style game. Showing the first and last letter and every occurrences of these letters inside the word
from random import choice
from unicodedata import normalize, category
#List of the words. In next list the game will use several modules for other lists
words = [
'οικονομία', 'δημοκρατία', 'διακρίσεις', 'αναζήτηση', 'κληρονομιά', 'ανακατασκευή', 'μνημεία', 'διαπραγμάτευση', 
'στρατηγική', 'προσαρμογή', 'επανάσταση', 'ιστορικά', 'κατανόηση', 'εξιστόρηση', 'ανασκαφές', 'υπεράσπιση', 'ποίηση', 
'σύνταξη', 'ερείπια', 'μυθολογία', 'αρχαίος', 'εκπαίδευση', 'ρητορική', 'συγκρούσεις', 'προστασία', 'γραμματική', 'αρχιτεκτονική',
'επικοινωνία', 'ετυμολογία', 'δημιουργία', 'σύνθεση', 'επανάκτηση', 'πολιτισμός', 'αξίες', 'φράσεις', 'κιονόκρανο', 'τέχνη', 'κοινωνία',
'περιγραφή', 'προϊστορική', 'κλασική', 'κατοχή', 'οθωμανοί', 'διαίρεση', 'λογοτεχνία', 'διαχείριση', 'θεωρία', 'τάφος', 'αμφιθέατρο',
'πολιτιστική', 'εξέλιξη', 'αναπαράσταση', 'συνεργασία', 'μετασχηματισμός', 'εξερεύνηση', 'μεταφορά', 'επιστήμη', 'προκλήσεις', 'φιλολογία',
'επαναφορά', 'ρήματα', 'ομοιότητα', 'σύνθετες', 'συνειδητοποίηση', 'μεσοπολέμου', 'διεκδίκηση', 'συλλαβισμός', 'άγαλμα', 'αρχαιολόγος', 'αναφορά',
'συστάσεις', 'επίθετα', 'τεχνολογία', 'μεταφορές', 'ιδέες', 'ανάλυση', 'επικό', 'κατάκτηση', 'συνεισφορά', 'σύνδεση', 'φιλοσοφία', 'εφορία',
'προτάσεις', 'παρομοιώσεις', 'αναπαλαίωση', 'παράδοση', 'κατάληψη', 'έλεγχος', 'ραψωδός', 'λεξιλόγιο', 'ιστορία', 'έρευνα', 'αντίθεση',
'πρακτική', 'ανακάλυψη', 'φάλαγγα', 'επιρρήματα', 'αποκατάσταση'
]
greek_letters = ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω']


def hangman_game(lista:list):
    points = 70
    chosen_word = choice(lista)
    remaining_letters = set(remove_accents(chosen_word)) - {remove_accents(chosen_word)[0], remove_accents(chosen_word)[-1]}
    print("The word to choose is", showing_word(chosen_word)[0])
    guess_letters = {remove_accents(chosen_word[0]), remove_accents(chosen_word[-1])}

    while len(remaining_letters) !=0:
        guessed_letter = input_letters()

        if guessed_letter in remaining_letters:
            remaining_letters = remaining_letters - {guessed_letter}
            guess_letters.add(guessed_letter)
            print(showing_word(chosen_word,guess_letters))         
        else:
            print(f"The letter {guessed_letter} is not in the word")
            points -= 10
    if len(remaining_letters) == 0:
        print(f'Μπράβο βρήκες τη λέξη {chosen_word}')
        if points > 0:
            print(f"Κέρδισες {points} πόντους")
        else:
            print("Έκανες πολλές προσπάθειες για να βρεις τη συγκεκριμένη λέξη άρα δεν κέρδισες πόντους")




def showing_word(word: str, revealed: set = None):
    if revealed is None:
        revealed = {remove_accents(word[0]), remove_accents(word[-1])}
    display = ""
    # Remove accents for comparison
    for  i, letter in enumerate(word):
        if remove_accents(letter) in revealed:
            display += letter
            display += " "
        else:
            display += "_ "
    return display, revealed

def remove_accents(word):
    # Normalize the word to decompose combined characters
    normalized_word = normalize('NFD', word.lower())  # Convert to lowercase for uniformity
    # Rebuild the word by filtering out non-spacing marks
    return ''.join(char for char in normalized_word if category(char) != 'Mn')
def input_letters():
    chosen_letter = input("Παρακαλώ μαντέψτε ένα γράμμα\t",)
    if chosen_letter in greek_letters:
        return chosen_letter
    else:
        print("Δεν επέλεξες ένα ελληνικό γράμμα της αλφαβήτου")
        input_letters()
    
    
def main():
    epilogi = 0
    while epilogi not in {1,2}:
        epilogi = input("""\nΓια να παίξετε κρεμάλα πατήστε 1 και enter \nΓια να σταματήσετε να παίζετε πατήστε 2 και enter""")
        if epilogi == "1":
            hangman_game(words)
        if epilogi == "2":
            break
            
if __name__ == "__main__":
    main()

