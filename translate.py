import mlflow_hf_transformers

from nltk import sent_tokenize
from transformers import pipeline

EXISTING_PAIRS = ['pt-en', 'en-pt']

LINKS_AND_MODELS = {'pt-en': 'link_here',
                    'en-pt': 'link_here'
                    }


def get_translation(text, lang_pair):
    if lang_pair in EXISTING_PAIRS:
        model, tokenizer = mlflow_hf_transformers.load_model(LINKS_AND_MODELS[lang_pair])
        source, target = lang_pair.split('-')
        translator = pipeline(
            "translation_{}_to_{}".format(source, target),
            model=model, tokenizer=tokenizer)
        print('loaded the model')
        sentences = sent_tokenize(text)
        result = []

        sentences = [x if x[-1] in '!?.' else x + '.' for x in sentences]

        for sent in sentences:
            sent = sent.replace('[', '')
            sent = sent.replace(']', '')
            result.append(translator(sent)[0]["translation_text"])

        if len(result) <= 512:
            result = ' '.join(result)

        return result
    else:
        print(f"Translation for language pair {lang_pair} is not possible.")
