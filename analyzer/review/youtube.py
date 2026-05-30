from analyzer.review.transcript import summarize_transcript_chunks
from analyzer.scrape.youtube import YoutubeScraper


class YoutubeSummarizer(YoutubeScraper):

    def __init__(self, chunks: int = 10):
        super().__init__()
        self.chunks = chunks

    def summarize(self, url: str):
        transcript = self.scrape(url)
        summary = summarize_transcript_chunks(transcript, self.chunks)
        return summary


if __name__ == "__main__":
    links = ["https://youtu.be/lVI_J1cbFb4?si=hfpY5dNaKmdLmm1r"]
    summarizer = YoutubeSummarizer()
    for link in links:
        print(summarizer.summarize(link))
