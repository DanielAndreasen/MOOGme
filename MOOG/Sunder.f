
      subroutine sunder(amol,i1,i2)
c******************************************************************************
c     This routine breaks up molecule amol into leftmost atom i1 and
c     the rest of the molecule i2
c******************************************************************************

      implicit real*8 (a-h,o-z)
      dimension itest(5)
      data itest/100000000,1000000,10000,100,1/
      im = amol

      do 1 i=1,5
         i1 = im/itest(i)
         if(i1 .eq. 0) go to 1
         i2 = im - i1*itest(i)
         return
1        continue

      return
      end
