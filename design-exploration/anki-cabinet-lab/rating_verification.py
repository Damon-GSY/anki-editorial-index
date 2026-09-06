"""Check real rating labels, including the legacy font-color add-on wrapper."""


class RatingVerification:
    def __init__(self, driver):
        self.d = driver
        self.cases = iter(("latte", "frappe", "macchiato", "mocha"))
        self.next_case()

    def next_case(self):
        flavor = next(self.cases, None)
        if flavor is None:
            self.d.production_addon._select_palette("latte")
            self.d.mw.resize(1280, 860)
            self.d.later(450, lambda: self.compatibility_case(2))
            return
        self.flavor = flavor
        self.d.production_addon._select_palette(flavor)
        self.d.later(450, self.check)

    def check(self):
        script = """(()=>{
          const canvas=document.createElement('canvas');canvas.width=canvas.height=1;
          const ctx=canvas.getContext('2d',{willReadFrequently:true});
          const rgb=c=>{ctx.clearRect(0,0,1,1);ctx.fillStyle=c;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].slice(0,3)};
          const lum=c=>rgb(c).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
          const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
          return [...document.querySelectorAll('#middle button[data-ease]')].map(button=>{
            const label=button.querySelector('font'),time=button.querySelector('.nobold');
            const b=getComputedStyle(button),l=getComputedStyle(label),t=getComputedStyle(time);
            const r=button.getBoundingClientRect(),tr=time.getBoundingClientRect();
            return {ease:button.dataset.ease,legacyColor:label.getAttribute('color'),
              label:l.color,button:b.color,font:l.fontFamily,weight:l.fontWeight,timeWeight:t.fontWeight,
              surface:b.backgroundColor,titleContrast:ratio(l.color,b.backgroundColor),timeContrast:ratio(t.color,b.backgroundColor),
              height:r.height,bottomGap:innerHeight-r.bottom,topGap:r.top,timeInside:tr.bottom<=r.bottom-8,
              clipped:r.right>innerWidth+1||r.left<0,onclick:button.getAttribute('onclick')};
          });
        })()"""
        self.d.js(script, self.after, self.d.mw.bottomWeb)

    def after(self, buttons):
        self.d.check(self.flavor + " legacy rating labels inherit Cabinet colors",
                     len(buttons) == 4 and all(b["label"] == b["button"] for b in buttons), buttons)
        self.d.check(self.flavor + " rating typography has a consistent hierarchy",
                     all("CabinetInter" in b["font"] and b["weight"] == "500" and b["timeWeight"] == "400" for b in buttons), buttons)
        self.d.check(self.flavor + " rating labels and intervals meet text contrast",
                     all(b["titleContrast"] >= 4.5 and b["timeContrast"] >= 4.5 for b in buttons), buttons)
        self.d.check(self.flavor + " rating padding stays inside native toolbar",
                     all(b["bottomGap"] >= 10 and b["topGap"] >= 8 and b["timeInside"] and not b["clipped"] for b in buttons), buttons)
        self.d.check(self.flavor + " native rating commands remain intact",
                     all(b["onclick"] == 'pycmd("ease' + b["ease"] + '");' for b in buttons))
        self.d.report.setdefault("rating_palette_checks", []).append({"flavor": self.flavor, "buttons": buttons})
        narrow = getattr(self, "narrow_checked", False) and self.flavor == "latte"
        self.d.capture("22-ratings-" + self.flavor + ("-820" if narrow else ""))
        if self.flavor == "latte" and not getattr(self, "narrow_checked", False):
            self.narrow_checked = True
            self.d.mw.resize(820, 760)
            self.d.later(450, self.check)
        else:
            self.d.mw.resize(1280, 860)
            self.next_case()

    def compatibility_case(self, count):
        # DOM compatibility fixture only: Anki's current scheduler always
        # supplies four ratings. Never dispatch these synthetic ease buttons.
        labels = {2: ["重来", "良好"], 3: ["重来", "良好", "简单"],
                  4: ["重来", "困难", "良好", "简单"]}[count]
        import json
        script = """(()=>{const labels=LABELS, times=['20 分','1 个月','1.2 个月','1.7 个月'];
          document.querySelector('#middle').innerHTML='<center><table cellpadding=0 cellspacing=0><tr>'+
            labels.map((label,i)=>'<td><button data-ease="'+(i+1)+'"><font color="red" face="serif"><b>'+label+'</b></font><span class="nobold">'+times[i]+'</span></button></td>').join('')+
            '</tr></table></center>';return true;})()""".replace("LABELS", json.dumps(labels))
        self.d.js(script, lambda _: self.d.later(250, lambda: self.check_compatibility(count)), self.d.mw.bottomWeb)

    def check_compatibility(self, count):
        def after(buttons):
            self.d.check(str(count) + "-button DOM fixture preserves rating color semantics",
                         len(buttons) == count and all(b["semanticMatches"] and b["wrapperMatches"] for b in buttons), buttons)
            if count < 4:
                self.compatibility_case(count + 1)
            else:
                from pathlib import Path
                path = Path(self.d.report["screenshots"][0]).parent / "23-ratings-chinese-preview.png"
                self.d.check("Chinese rating footer preview captured", self.d.mw.bottomWeb.grab().save(str(path)))
                self.d.report["screenshots"].append(str(path))
                self.d.mw.reviewer._showEaseButtons()
                self.d.later(350, self.d.rate_buttons)
        self.d.js("""(()=>{const buttons=[...document.querySelectorAll('#middle button[data-ease]')];
          const tokens=buttons.length===4?['--cb-again','--cb-learn','--cb-review','--mist-easy']:['--cb-again','--cb-review','--mist-easy'];
          return buttons.map((b,i)=>{const s=getComputedStyle(b),w=getComputedStyle(b.querySelector('font b'));
            return {ease:b.dataset.ease,semanticMatches:s.getPropertyValue('--cb-rating').trim()===s.getPropertyValue(tokens[i]).trim(),
              wrapperMatches:w.color===s.color&&w.fontFamily===s.fontFamily&&w.fontWeight==='500'};});})()""", after, self.d.mw.bottomWeb)
