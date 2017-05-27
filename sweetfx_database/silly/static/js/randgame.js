
function RandGame(targetid, targeturl) {
    this.next;
    this.targetlist = $(targetid);
    this.targeturl = targeturl;

    this.start = function (num)
    {
        var parent = this;

        $.get(parent.targeturl + "?num="+num, function (data) {
            parent.targetlist.empty();
            var x;
            for (x in data) {
                var li = $("<li/>").text(data[x]);
                parent.targetlist.append(li);

            }
            parent.get_one();
        });
    }

    this.get_one = function () {
        var parent = this;

        $.get(parent.targeturl, function (data) {
            parent.next = data[0];
        });

        if (this.next) {
            var oli = this.targetlist.find("li:first");
            oli.slideUp(1000, function() {
               oli.remove();
            });
            var li=$("<li/>").text(this.next);
            li.hide();
            this.targetlist.append(li);
            li.slideDown(1000);
        }

        setTimeout(function () {
            parent.get_one();
        }, 7000);
    }
}
