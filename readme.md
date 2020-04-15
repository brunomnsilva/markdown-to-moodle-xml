# Markdown to Moodle XML 

This tool allows you to create *multiple choice* questions through *markdown* syntaxe, producing Moodle XML files that can be directly imported in the platform.

Currently, it allows:

- Defining questions categories;
- One or more correct answers;
- Inclusion of *inline* and *block* code snippets;
- Inclusion of *latex* math formulas;
- Inclusion of images (local and from the *web*)
- **New!** Automatic conversion of block code snippets to image format; use `{img}` after the *lexer*, e.g.:
    ```
        ```cpp{img}
        int vec[] = {1,2,3,4,5,6,7,8};
        int *p = vec + 1;
        ```
    ```

For the following example, the outputs are presented at the end of this *readme*:
```markdown
# Dummy Category 1

* What is the color of the sky?
    - red
    - green
    - !blue
    - yellow

* Which ones are programmer's text editor?
    - !sublime text
    - !vim
    - !atom
    - microsoft word

# Dummy Category 2

* Who is the main protagonist in Dragon Ball?
    - !Son Goku
    - Picolo
    - Son Gohan
    - Vegeta

* Look at this code:
`` ```javascript
var a = 5
let b = 6
const c = 7
`` ```
Which one is immutable?
    - `a`
    - $b$ 
    - !c

* Look at this code:
`` ```cpp
#include <stdio.h>

int main() {
    int a = 1, b = 2;
    if(a < b )
        printf("Hello a World \n");
    else
        printf("Hello b World \n");
    return EXIT_SUCCESS;
}
`` ```
Does this code compile?
    - !Yes
    - No

* What is this?
    ![turtle](turtle.png)
    - !A turtle
    - A bird

* How do you spell $\alpha + \beta$?
    - a plus b
    - !alpha plus beta
    - a fish and a funny flag
```

## Why?

* Because writing quizes in `markdown` format is more pleasant than write it in `ms-office`, `libre-office` or `GIFT format`.
  - I personally use *VS Code* with out-of-the-box markdown preview support.
* Because our live is too short to copy-pasting the quizes into moodle!

## How to use?

Simply cast: `python m2m.py <your-md-file>`

## Can I try it?

Sure, cast this: `python m2m.py example.md`

New files will be created: `example-DummyCategory1.xml` and `example-DummyCategory2.xml`

## Is there anything special with the markdown file?

Yes.

* First, I treat `# section` as beginning of new question bank, with `section` has the *category* of the following questions.
* Second, I treat `* question` as question. A question can contains multi-line string
* Third, I treat ` - answer` as wrong answer and ` - !answer` as correct answer. The correct answer has an exclamation mark at the beginning
* Any line preceeded by triple backtick will be converted to `<pre>` or `</pre>`
* Any `![]()` will be converted into `<img src="data:image/png,base64,..."/>`
* Any `$latex$` or `$$latex$$` will be converted into `\(\)`
* Any inline code will be translated wrapped inside `<code>` tag

## Prerequisites

* Python
* `markdown` python package (`pip install markdown --user`)
* Human, non-muggle

## Improvements / Fixes from this fork

This fork makes the following changes and/or improvements:

- `[DONE]` Allow different answer numbering from allowed values: 'none', 'abc', 'ABCD' or '123'
- `[DONE]` Usage of prefix '!' in answer to mark it as correct (instead of space at the end)
- `[DONE]` Usage of section name for quiz category (adds a dummy question, as per Moodle spec.)
  - This only works if you have "Get category from file" checked, when importing in Moodle
- `[FIX]`  Output of inline code should be wrapped only inside `<code>` tag
- `[DONE]` Allow code formatting in answers for single block code and single dollar math 
- `[DONE]` Output file based on (input filename + section text), but further sanitized
- `[DONE]` Use of MD5 hash for question names instead of SHA224 -- more compact in Moodle view
  - Probability of collision should remain fairly low within the expected question bank size)
- `[FIX]` Fix html escaping for <, > and & inside code blocks

## Sample Moodle XML Outputs

Output for category "Dummy Category 1":

```xml
<?xml version="1.0" ?>
<quiz>
    <question type="category">
        <category>
            <text>Dummy Category 1</text>
        </category>
    </question>
    <question type="multichoice">
        <name>
            <text>0001ca41c468595917f8db53401016a17806</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[<p>What is the color of the sky?</p>]]></text>
        </questiontext>
        <answer fraction="0">
            <text>red</text>
        </answer>
        <answer fraction="0">
            <text>green</text>
        </answer>
        <answer fraction="100.0">
            <text>blue</text>
        </answer>
        <answer fraction="0">
            <text>yellow</text>
        </answer>
        <shuffleanswers>1</shuffleanswers>
        <single>true</single>
        <answernumbering>abc</answernumbering>
    </question>
    <question type="multichoice">
        <name>
            <text>0002b1b432fc13953e0639afed9a294c912d</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[<p>Which ones are programmer's <code>text editor</code>?</p>]]></text>
        </questiontext>
        <answer fraction="33.3333333">
            <text>sublime text</text>
        </answer>
        <answer fraction="33.3333333">
            <text>vim</text>
        </answer>
        <answer fraction="33.3333333">
            <text>atom</text>
        </answer>
        <answer fraction="0">
            <text>microsoft word</text>
        </answer>
        <shuffleanswers>1</shuffleanswers>
        <single>false</single>
        <answernumbering>abc</answernumbering>
    </question>
    <question type="multichoice">
        <name>
            <text>0003e03a957a6dbc75372b9b894392eed107</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[<p>What is this?<img style="display:block;" src="data:image/png;base64,iVBORw..." /></p>]]></text>
        </questiontext>
        <answer fraction="100.0">
            <text>A turtle</text>
        </answer>
        <answer fraction="0">
            <text>A bird</text>
        </answer>
        <shuffleanswers>1</shuffleanswers>
        <single>true</single>
        <answernumbering>abc</answernumbering>
    </question>
</quiz>
```

Output for category "Dummy Category 2":

```xml
<?xml version="1.0" ?>
<quiz>
    <question type="category">
        <category>
            <text>Dummy Category 2</text>
        </category>
    </question>
    <question type="multichoice">
        <name>
            <text>0001340edd40c654d705576e050bbedf67fb</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[<p>Who is the main protagonist in Dragon Ball?</p>]]></text>
        </questiontext>
        <answer fraction="100.0">
            <text>Son Goku</text>
        </answer>
        <answer fraction="0">
            <text>Picolo</text>
        </answer>
        <answer fraction="0">
            <text>Son Gohan</text>
        </answer>
        <answer fraction="0">
            <text>Vegeta</text>
        </answer>
        <shuffleanswers>1</shuffleanswers>
        <single>true</single>
        <answernumbering>abc</answernumbering>
    </question>
    <question type="multichoice">
        <name>
            <text>0002208e45e4a90f41bba61271891e44fab3</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[<p>Look at this code:<pre><code>var a = 5
let b = 6
const c = 7
</code></pre>
Which one is immutable?</p>]]></text>
        </questiontext>
        <answer fraction="0">
            <text><![CDATA[<p>Variable <code>a</code></p>]]></text>
        </answer>
        <answer fraction="0">
            <text><![CDATA[<p>b as in \(b\)</p>]]></text>
        </answer>
        <answer fraction="100.0">
            <text>c</text>
        </answer>
        <shuffleanswers>1</shuffleanswers>
        <single>true</single>
        <answernumbering>abc</answernumbering>
    </question>
    <question type="multichoice">
        <name>
            <text>0003ef08d0d95e79790317ba892e0916c594</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[<p>Look at this code:<pre><code>#include &lt;stdio.h&gt;
int main() {
    int a = 1, b = 2;
    if(a &lt; b )
        printf("Hello a World \n");
    else
        printf("Hello b World \n");
    return EXIT_SUCCESS;
}
</code></pre>
Does this code compile?</p>]]></text>
        </questiontext>
        <answer fraction="100.0">
            <text>Yes</text>
        </answer>
        <answer fraction="0">
            <text>No</text>
        </answer>
        <shuffleanswers>1</shuffleanswers>
        <single>true</single>
        <answernumbering>abc</answernumbering>
    </question>
    <question type="multichoice">
        <name>
            <text>000476982886ab058e51e75d5d036ef67218</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[<p>What is this?<img style="display:block;" src="data:image/png;base64,iVBO..." /></p>]]></text>
        </questiontext>
        <answer fraction="100.0">
            <text>A turtle</text>
        </answer>
        <answer fraction="0">
            <text>A bird</text>
        </answer>
        <shuffleanswers>1</shuffleanswers>
        <single>true</single>
        <answernumbering>abc</answernumbering>
    </question>
    <question type="multichoice">
        <name>
            <text>000576341a92709dba73f9e5c5ea3318374e</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[<p>How do you spell \(\alpha + \beta\)?</p>]]></text>
        </questiontext>
        <answer fraction="0">
            <text>a plus b</text>
        </answer>
        <answer fraction="100.0">
            <text>alpha plus beta</text>
        </answer>
        <answer fraction="0">
            <text>a fish and a funny flag</text>
        </answer>
        <shuffleanswers>1</shuffleanswers>
        <single>true</single>
        <answernumbering>abc</answernumbering>
    </question>
</quiz>
```