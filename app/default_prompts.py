DEFAULT_TRANSLATION_IMAGE_PROMPT = ('You will receive a screenshot that may contain text in any language. Please do the following directly:\n'
 '1. Recognize the text in the image;\n'
 '2. Translate it into {target_language};\n'
 '3. Preserve paragraph order and reading order as much as possible;\n'
 '4. Do not explain, do not add preface, and do not output the original text;\n'
 '5. If some text is unclear, translate as much as possible based on visible content and mark it as partially '
 'unclear;\n'
 '6. Output clean translated text suitable for direct reading.')

DEFAULT_TRANSLATION_TEXT_PROMPT = ('Translate the provided text into {target_language}. Preserve paragraph order and line breaks when reasonable. Do not '
 'explain the translation, do not add preface, and do not output the original text. If part of the text is unclear, '
 'translate as much as possible and mention that it is partially unclear.')

DEFAULT_ANSWER_IMAGE_PROMPT = ('You will receive a screenshot that may contain a question, exercise, prompt, or problem statement. Understand the '
 'visible content carefully and answer in {target_language}. If the screenshot contains constraints, options, or '
 'context, incorporate them into the answer. Keep the response direct, correct, and concise, and clearly state when '
 'the visible information is insufficient.')

DEFAULT_ANSWER_TEXT_PROMPT = ('Answer or explain the provided text in {target_language}. If the text is a question, solve it directly. If it is a '
 'request for explanation, explain it clearly. Keep the response concise but complete, and clearly state when the '
 'provided information is insufficient.')

DEFAULT_POLISH_IMAGE_PROMPT = ('You will receive a screenshot containing text. Recognize the text and rewrite it into polished, natural '
 '{target_language}. Preserve the original meaning and key details while improving clarity, fluency, and wording. '
 'Output only the polished result.')

DEFAULT_POLISH_TEXT_PROMPT = ('Rewrite the provided text into polished, natural {target_language}. Preserve the original meaning and important '
 'details while improving clarity, fluency, and tone. Output only the polished result.')

DEFAULT_PROMPT = ('You will receive a screenshot that may contain text in any language. Please do the following directly:\n'
 '1. Recognize the text in the image;\n'
 '2. Translate it into {target_language};\n'
 '3. Preserve paragraph order and reading order as much as possible;\n'
 '4. Do not explain, do not add preface, and do not output the original text;\n'
 '5. If some text is unclear, translate as much as possible based on visible content and mark it as partially '
 'unclear;\n'
 '6. Output clean translated text suitable for direct reading.')

DEFAULT_PROMPT_PRESET_DEFINITIONS = [{'name': '翻譯',
  'builtin_id': 'translate',
  'image_prompt': 'You will receive a screenshot that may contain text in any language. Please do the following '
                  'directly:\n'
                  '1. Recognize the text in the image;\n'
                  '2. Translate it into {target_language};\n'
                  '3. Preserve paragraph order and reading order as much as possible;\n'
                  '4. Do not explain, do not add preface, and do not output the original text;\n'
                  '5. If some text is unclear, translate as much as possible based on visible content and mark it as '
                  'partially unclear;\n'
                  '6. Output clean translated text suitable for direct reading.',
  'text_prompt': 'Translate the provided text into {target_language}. Preserve paragraph order and line breaks when '
                 'reasonable. Do not explain the translation, do not add preface, and do not output the original text. '
                 'If part of the text is unclear, translate as much as possible and mention that it is partially '
                 'unclear.'},
 {'name': '解答',
  'builtin_id': 'answer',
  'image_prompt': 'You will receive a screenshot that may contain a question, exercise, prompt, or problem statement. '
                  'Understand the visible content carefully and answer in {target_language}. If the screenshot '
                  'contains constraints, options, or context, incorporate them into the answer. Keep the response '
                  'direct, correct, and concise, and clearly state when the visible information is insufficient.',
  'text_prompt': 'Answer or explain the provided text in {target_language}. If the text is a question, solve it '
                 'directly. If it is a request for explanation, explain it clearly. Keep the response concise but '
                 'complete, and clearly state when the provided information is insufficient.'},
 {'name': '潤色',
  'builtin_id': 'polish',
  'image_prompt': 'You will receive a screenshot containing text. Recognize the text and rewrite it into polished, '
                  'natural {target_language}. Preserve the original meaning and key details while improving clarity, '
                  'fluency, and wording. Output only the polished result.',
  'text_prompt': 'Rewrite the provided text into polished, natural {target_language}. Preserve the original meaning '
                 'and important details while improving clarity, fluency, and tone. Output only the polished result.'}]
