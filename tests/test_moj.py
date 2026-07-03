# pylint: disable=import-error

from textwrap import dedent

from fin_rag.moj import parse_moj_law_html


def test_parse_moj_law_html_extracts_revision_date_and_article_text() -> None:
    html = dedent(
        """
        <html>
          <body>
            <table>
              <tr>
                <th>法規名稱：</th>
                <td><a id="hlLawName">測試辦法（113.01.01 修正）</a></td>
              </tr>
              <tr id="trLNNDate">
                <th>修正日期：</th>
                <td>民國 113 年 12 月 25 日 </td>
              </tr>
            </table>
            <div id="pnLawFla" class="well law-reg law-content">
              <div class="law-reg-content">
                <div class="row">
                  <div class="col-no"><a name="1">第 1 條</a></div>
                  <div class="col-data">
                    <div class="law-article">
                      <div class="line-0000 show-number">第一項文字。</div>
                      <div class="line-0004">一、子項目。</div>
                    </div>
                  </div>
                </div>
                <div class="row">
                  <div class="col-no"><a name="2">第 2 條</a></div>
                  <div class="col-data">
                    <div class="law-article">
                      <div class="line-0000">第二條內容。</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </body>
        </html>
        """
    )

    document = parse_moj_law_html(html)

    assert document.title == "測試辦法"
    assert document.revision_date == "113-12-25"
    assert document.text == dedent(
        """
        第 1 條
        第一項文字。
        一、子項目。

        第 2 條
        第二條內容。
        """
    ).strip()
