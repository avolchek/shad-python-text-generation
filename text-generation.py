import os
import nltk
from collections import defaultdict
import pickle
from functools import partial
import random
import textwrap


def is_punctuation(token):
    return token in [',', '.', '!', '?', ';', ':', '...']


def is_sentence_end(token):
    return token in ['.', '!', '?', '...']


def find_text_files(path):
    result = []
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)

        if os.path.isdir(full_path):
            result += find_text_files(full_path)
        elif os.path.isfile(full_path) and os.path.splitext(full_path)[1] == '.txt':
            result += [full_path]

    return result


def process_corpus(path, processing_function):
    text_files = find_text_files(path)

    words_count = 0

    for file_number, file_name in enumerate(text_files):

        print 'processing file #{} from {}: {}'.format(file_number + 1, len(text_files), file_name)
        print 'already processed words = {}'.format(words_count)
        print ''

        with open(file_name, 'r') as f:
            file_content = f.read()
            sents = nltk.sent_tokenize(file_content)
            sents = map(nltk.word_tokenize, sents)
            sents = filter(lambda s: is_sentence_end(s[-1]), sents)
            tokens = [word for sent in sents for word in sent]

            def sanitize_token(token):
                if token in ['.', '!', '?', '...', ',', ';', ':']:
                    return token
                return token.lower() if token.isalpha() else ''

            tokens = map(sanitize_token, tokens)
            tokens = filter(len, tokens)

            words_count += len(tokens)

            processing_function(tokens)


def compute_corpus_statistics(path):

    two_words_statistics = defaultdict(partial(defaultdict, int))
    one_word_statistics = defaultdict(partial(defaultdict, int))

    def process_compute_words_stats(tokens):
        for i in xrange(len(tokens) - 2):
            key = (tokens[i], tokens[i + 1])
            two_words_statistics[key][tokens[i + 2]] += 1

        for i in xrange(len(tokens) - 1):
            one_word_statistics[tokens[i]][tokens[i + 1]] += 1

    process_corpus(path, process_compute_words_stats)

    with open('one_word_statistics.p', 'w') as fp:
        pickle.dump(one_word_statistics, fp)

    with open('two_words_statistics.p', 'w') as fp:
        pickle.dump(two_words_statistics, fp)


def generate_text(paragraphs_count):
    one_word_statistics = {}
    two_words_statistics = {}

    with open('one_word_statistics.p', 'r') as fp:
        one_word_statistics = pickle.load(fp)

    with open('two_words_statistics.p', 'r') as fp:
        two_words_statistics = pickle.load(fp)

    def choice_from_dict(d):
        score_sum = sum(d.values())
        rnd = random.randint(1, score_sum)
        for word, score in d.items():
            if score >= rnd:
                return word
            rnd -= score

    def generate_sentence():
        sentence = []

        first_word = random.choice(one_word_statistics.keys())
        sentence.append(first_word.title())

        second_word = choice_from_dict(one_word_statistics[first_word])
        sentence.append(second_word)

        while not is_sentence_end(second_word):
            new_word = choice_from_dict(two_words_statistics[(first_word, second_word)])
            sentence.append(new_word)
            first_word, second_word = second_word, new_word

        return sentence

    def generate_paragraph(min_sentences_count, max_sentences_count):
        sentences_count = random.randrange(min_sentences_count, max_sentences_count)

        paragraph = []
        for i in xrange(sentences_count):
            paragraph += generate_sentence()

        return paragraph

    def tokens_to_string(tokens):
        string_result = tokens[0]
        for tk in tokens[1:]:
            if not is_punctuation(tk):
                string_result += ' '
            string_result += tk

        return string_result

    result = [tokens_to_string(generate_paragraph(3, 30)) for _ in xrange(paragraphs_count)]

    return result


if __name__ == '__main__':
    """compute_corpus_statistics('corpus')


    sys.exit(0)
    """

    text_paragraphs = generate_text(200)

    text_paragraphs = map(partial(textwrap.fill, initial_indent='\t'), text_paragraphs)
    text = '\n'.join(text_paragraphs)

    print(text)
