import layoutparser as lp


class PdfParser:
    def __init__(self, input_pdf, dpi=72):
        self.input_pdf = input_pdf
        self.dpi = dpi
        self.pdf_base_layout, self.pdf_images = self._load_pdf()
        self.model = self._load_model()

    def _load_pdf(self):
        return lp.load_pdf(self.input_pdf, load_images=True, dpi=self.dpi)

    def _load_model(self):
        return lp.Detectron2LayoutModel(
            "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config",
            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.7],
            label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
        )

    def detect_layout(self, page_idx):
        return self.model.detect(self.pdf_images[page_idx])

    @staticmethod
    def text_blocks_to_text_list(text_blocks, coalesce_threshold=1):
        if not text_blocks:
            return []

        words = [text_blocks[0].text]
        prev_x_2 = text_blocks[0].block.x_2

        for block in text_blocks[1:]:
            gap_x = block.block.x_1 - prev_x_2
            if gap_x > coalesce_threshold:
                words.append(block.text)
            else:
                words[-1] += block.text
            prev_x_2 = block.block.x_2

        return words

    @staticmethod
    def is_overlapping(block1, block2):
        if block1.x_2 <= block2.x_1 or block1.x_1 >= block2.x_2:
            return False

        if block1.y_2 <= block2.y_1 or block1.y_1 >= block2.y_2:
            return False

        return True

    @staticmethod
    def non_overlapping_blocks(blocks):
        # sort by score desc
        blocks = sorted(blocks, key=lambda x: x.score, reverse=True)

        # remove overlapping blocks
        result = []
        for block in blocks:
            if any([PdfParser.is_overlapping(block.block, b.block) for b in result]):
                continue
            result.append(block)

        return result

    def extract_paragraphs(self, page_idx):
        width = self.pdf_images[page_idx].width
        height = self.pdf_images[page_idx].height
        word_blocks = self.pdf_base_layout[page_idx].get_homogeneous_blocks()
        layout = self.detect_layout(page_idx)
        paragraph_blocks = [b for b in layout if b.type in ["Text", "List"]]
        paragraph_blocks = self.non_overlapping_blocks(paragraph_blocks)
        paragraph_blocks = sorted(
            paragraph_blocks,
            key=lambda x: (x.block.x_1 // (width / 8), x.block.y_1 // (height / 80)),
        )

        paragraphs = []
        for paragraph_block in paragraph_blocks:
            word_blocks_in_paragraph = list(
                filter(
                    lambda x: x.block.is_in(paragraph_block.block, center=True),
                    word_blocks,
                )
            )
            text = self.text_blocks_to_text_list(word_blocks_in_paragraph)
            if len(text) > 10:
                paragraphs.append(" ".join(text))
        return paragraphs

    def extract_paragraphs_all(self):
        paragraphs = []
        for page_idx in range(len(self.pdf_images)):
            paragraphs.extend(self.extract_paragraphs(page_idx))
        return paragraphs
