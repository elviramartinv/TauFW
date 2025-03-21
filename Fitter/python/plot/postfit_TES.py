#! /usr/region/env python
# Author: @oponcet (Sept 2024)
import os, sys, re
#sys.path.append('../plots')
from TauFW.common.tools.file import ensuredir
from TauFW.common.tools.root import ensureTFile #, gethist
from TauFW.common.tools.utils import repkey
from TauFW.Plotter.plot.utils import LOG, grouphists
from TauFW.Plotter.plot.Stack import Stack # Var
from TauFW.Plotter.sample.utils import CMSStyle, setera
import TauFW.Plotter.sample.SampleStyle as STYLE
from ROOT import kBlack,TCanvas


# SET NEGATIVE BINS TO ZERO
def set_negative_bins_to_zero(hist):
    """Set negative bins to zero in the given histogram."""
    for bin in range(1, hist.GetNbinsX() + 1):
        if hist.GetBinContent(bin) < 0:
            hist.SetBinContent(bin, 0)
            hist.SetBinError(bin, 0)  # Optional: Set bin error to zero if desired


def drawpostfit(fname,region,procs,**kwargs):
  """Plot pre- and post-fit plots PostFitShapesFromWorkspace."""
  print(">>>\n>>> drawpostfit(%r,%r)"%(fname,region))
  outdir    = kwargs.get('outdir',  ""         )
  pname     = kwargs.get('pname',   "$FIT_%s.png" ) # replace $FIT = 'prefit', 'postfit' 
  ratio     = kwargs.get('ratio',   True       )
  tag       = kwargs.get('tag',     ""         )
  xtitle    = kwargs.get('xtitle',  None       )
  title     = kwargs.get('title',   None       )
  text      = kwargs.get('text',    ""         )
  tsize     = kwargs.get('tsize',   0.050      )
  xmin      = kwargs.get('xmin',    None       )
  xmax      = kwargs.get('xmax',    None       )
  ymargin   = kwargs.get('ymargin', 1.22       )
  groups    = kwargs.get('group',   [ ]        )
  position  = kwargs.get('pos',     None       ) # legend position
  ncol      = kwargs.get('ncol',    None       ) # legend columns
  square    = kwargs.get('square',  False      )
  era       = kwargs.get('era',     ""         )
  exts      = kwargs.get('exts', ['pdf','png','root'] ) # figure extension
  text      = kwargs.get('text',    ""         )
  ymax      = None
  fits      = ['prefit','postfit']
  file      = ensureTFile(fname,'READ')
  if outdir:
    ensuredir(outdir)
  if era:
    setera(era)

  if text != "":
      print(text)
      text = "#mu#tau_{h}: " + text
  else:
      text = "#mu#tau_{h}"

  print(">>>   era = %r"%(era))
  CMSStyle.setCMSEra(era, cms="CMS", extra="Preliminary") 
  CMSStyle.setTDRStyle()
  # canvas = TCanvas("canvas","canvas",100,100,800,800)
  # CMSStyle.setCMSLumiStyle(canvas,3,outOfFrame=False,verbosity=2) # 

  
  # DRAW PRE-/POST-FIT
  for fit in fits:
    print(">>>   fit = %r"%(fit))
    fitdirname = "%s_%s"%(region,fit)
    dir = file.Get(fitdirname)
    if not dir:
      LOG.warning('drawpostfit: Did not find dir "%s"'%(fitdirname),pre="   ")
      return
    obshist = None
    exphists = [ ]
    
    # GET HIST
    for proc in procs: #reversed(samples):
      hname = "%s/%s"%(fitdirname,proc)
      hist  = file.Get(hname)
      if not hist:
        LOG.warning('drawpostfit: Could not find "%s" template in directory "%s_%s"'%(proc,region,fit),pre="   ")
        continue

      print(f">>>   Successfully retrieved histogram for {proc}")

      # Set negative bin values to zero
      set_negative_bins_to_zero(hist)
      groups  = [
      # (['^TT*'],'Top','ttbar'), #,STYLE.sample_colors['TT']),
      (['^TT*','ST*'],'Top','ttbar and single top'),

      ]

      if 'data_obs' in proc:
        obshist = hist
        hist.SetLineColor(1)
        hist.SetMarkerStyle(20)
        ymax = hist.GetMaximum()*ymargin
      else:
        exphists.append(hist)
      if proc in STYLE.sample_titles:
        hist.SetTitle(STYLE.sample_titles[proc])
      if proc in STYLE.sample_colors:
        hist.SetFillStyle(1001)
        hist.SetFillColor(STYLE.sample_colors[proc])
    if len(exphists)==0:
      LOG.warning('drawpostfit: Could not find any templates in directory "%s"'%(region),pre="   ")
      continue
    if not obshist:
      LOG.warning('drawpostfit: Could not find a data template in directory "%s"'%(region),pre="   ")
      continue
    for groupargs in groups:
      grouphists(exphists,*groupargs,replace=True)
    
    # PLOT
    xtitle     = (xtitle or exphists[0].GetXaxis().GetTitle()) #.replace('[GeV]','(GeV)')
    xmax       = xmax or exphists[0].GetXaxis().GetXmax()
    xmin       = xmin or exphists[0].GetXaxis().GetXmin()
    errtitle   = "Pre-fit stat. + syst. unc." if fit=='prefit' else "Post-fit unc."
    ytitle     = "Events/10 GeV" # hardcoded for paper
    # pname_     = repkey(pname,FIT=fit,ERA=era)+region
    pname_ = fit + "_"+region
    rmin, rmax = (0.28,1.52)
    print(" pname_ = %r"%(pname_))

   

    print(">>>   Draw %s"%(pname_))
    plot = Stack(xtitle,obshist,exphists)
    plot.draw(xmin=xmin,xmax=xmax,ymax=ymax,square=square,ratio=ratio,rmin=rmin,rmax=rmax,
              staterror=True,errtitle=errtitle,lcolors=kBlack,xtitle="m_{vis}[GeV]",ytitle=ytitle)
    plot.drawtext(text)
    plot.drawlegend(position,tsize=tsize,ncol=ncol)
    if title:
      plot.drawtext(title,bold=False,position="right")
    plot.saveas(pname_,outdir=outdir,ext=exts)
    print(">>>   Saved %s"%(pname_))
    # plot.close()
    print(">>>   Done for fit %s"%(fit))
  
  print("Done.")
  
  file.Close()
  