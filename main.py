from judges.technical_judge import evaluate as tech_eval
from judges.legal_judge import evaluate as legal_eval
from judges.ethics_judge import evaluate as ethics_eval
from council.arbitrator import combine

def run():

    input_data = "sample AI output"

    r1 = tech_eval(input_data)
    r2 = legal_eval(input_data)
    r3 = ethics_eval(input_data)

    final = combine([r1, r2, r3])

    print(final)

if __name__ == "__main__":
    run()
